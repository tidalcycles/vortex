from fractions import Fraction

from parsimonious import NodeVisitor
from parsimonious.nodes import Node

from vortex.control import n, s
from vortex.pattern import id, polymeter, polyrhythm, pure, sequence, silence, timecat
from vortex.utils import flatten


class MiniVisitor(NodeVisitor):
    def visit_start(self, _node, children):
        _, element, _ = children
        return element

    def visit_sequence(self, _node, children):
        element, other_elements = children
        if isinstance(other_elements, Node):
            other_elements = []
        other_elements = [e for _, e in other_elements]
        return dict(type="sequence", elements=[element] + other_elements)

    def visit_element(self, _node, children):
        value, euclid_modifier, modifiers = children
        element = dict(
            type="element",
            value=value,
            modifiers=modifiers,
        )
        if not isinstance(euclid_modifier, Node):
            element["euclid_modifier"] = euclid_modifier[0]
        return element

    def visit_element_value(self, _node, children):
        return children[0]

    def visit_polyrhythm_subseq(self, _node, children):
        seqs = children[2]
        return dict(type="polyrhythm", seqs=seqs)

    def visit_polymeter_subseq(self, _node, children):
        seqs = children[2]
        steps = children[5]
        if isinstance(steps, Node):
            steps = 1
        else:
            steps = steps[0]
        return dict(type="polymeter", seqs=seqs, steps=steps)

    def visit_polymeter_steps(self, _node, children):
        _, number = children
        return number

    def visit_polymeter1_subseq(self, _node, children):
        seqs = children[2]
        return dict(type="polymeter", seqs=seqs, steps=1)

    def visit_subseq_body(self, _node, children):
        # sequence (ws? ',' ws? sequence)*
        seq, other_seqs = children
        if isinstance(other_seqs, Node):
            other_seqs = []
        other_seqs = [s[3] for s in other_seqs]
        return [seq] + other_seqs

    ##
    # Terms
    #

    def visit_term(self, _node, children):
        # Workaround to return an AST element "number" for numbers
        if not isinstance(children[0], dict):
            return dict(type="number", value=children[0])
        return children[0]

    def visit_rest(self, _node, _children):
        return dict(type="rest")

    def visit_word_with_index(self, _node, children):
        word, index = children
        index = 0 if isinstance(index, Node) else index[0]
        return dict(type="word", value=word, index=index)

    def visit_index(self, _node, children):
        _, number = children
        return number

    ##
    # Modifiers
    #

    def visit_euclid_modifier(self, _node, children):
        _, _, k, _, _, _, n, rotation, _, _ = children
        mod = dict(type="euclid_modifier", k=k, n=n)
        if not isinstance(rotation, Node):
            mod["rotation"] = rotation
        return mod

    def visit_euclid_rotation_param(self, _node, children):
        _, _, _, rotation = children
        return rotation

    def visit_modifiers(self, _node, children):
        mods = [m for m in children if m["op"] not in ("degrade", "weight")]

        # The degrade modifier (?) does not take into account application order,
        # so we merge them into a single modifier.
        degrade_mods = [m for m in children if m["op"] == "degrade"]
        deg_count = sum([m["count"] for m in degrade_mods])
        if deg_count:
            degrade_mod = dict(type="modifier", op="degrade", count=deg_count)
            mods.append(degrade_mod)

        # The weight modifier (@) can be duplicated, but only the last one is
        # used, all others are ignored.
        weight_mods = [m for m in children if m["op"] == "weight"]
        if weight_mods:
            mods.append(weight_mods[-1])

        return mods

    def visit_modifier(self, _node, children):
        return children[0]

    def visit_fast(self, _node, children):
        _, number = children
        return dict(type="modifier", op="fast", value=number)

    def visit_slow(self, _node, children):
        _, number = children
        return dict(type="modifier", op="slow", value=number)

    def visit_repeat(self, _node, children):
        n = len(children)
        return dict(type="modifier", op="repeat", count=n)

    def visit_degrade(self, _node, children):
        n = len(children)
        return dict(type="modifier", op="degrade", count=n)

    def visit_weight(self, _node, children):
        _, number = children
        return dict(type="modifier", op="weight", value=number)

    ##
    # Primitives
    #

    def visit_word(self, node, _children):
        return node.text

    def visit_number(self, node, children):
        return children[0]

    def visit_real(self, node, _children):
        return float(node.text)

    def visit_integer(self, node, _children):
        return int(node.text)

    def visit_pos_integer(self, node, _children):
        return int(node.text)

    ##
    # Others
    #

    def visit_ws(self, _node, _children):
        return

    def generic_visit(self, node, children):
        return children or node


class MiniInterpreter:
    def eval(self, node):
        node_type = node["type"]
        visit_method = getattr(self, f"visit_{node_type}")
        return visit_method(node)

    def visit_sequence(self, node):
        elements = [self.eval(n) for n in node["elements"]]
        tc_args = []
        # Because each element might have been replicated/repeated, each element
        # is actually a list of tuples (weight, pattern, degrade_ratio).
        for es in elements:
            # We extract the weight and degrade_ratio from the first element (it
            # does not matter from which element, all have the same state
            # values).
            weight = es[0][0] if es else 1
            deg_by = es[0][2] if es else 0
            # Use the length of the replicated element as weight times the
            # `weight` modifier (if present).  Build a sequence out of the
            # replicated elements and degrade by the accumulated degrade ratio.
            tc_args.append(
                (len(es) * weight, sequence(*[e[1] for e in es]).degrade_by(deg_by))
            )
        # Finally use timecat to create a pattern out of this sequence
        return timecat(*tc_args)

    def visit_polyrhythm(self, node):
        return polyrhythm(*[self.eval(seq) for seq in node["seqs"]])

    def visit_polymeter(self, node):
        return polymeter(*[self.eval(seq) for seq in node["seqs"]], steps=node["steps"])

    def visit_element(self, node):
        # Here we collect all modifier functions of an element and reduce them
        modifiers = [self.eval(m) for m in node["modifiers"]]
        pat = self.eval(node["value"])
        # Apply an euclid modifier if present
        if "euclid_modifier" in node:
            k, n, rotation = self.eval(node["euclid_modifier"])
            pat = pat.euclid(k, n, rotation)
        # The initial value is the tuple of 3 elements (see visit_modifier): a
        # default weight of 1, a "pure" pattern of the elements value and
        # degrade ratio of 0 (no degradation).  It is a list of tuples, because
        # modifiers return a list of tuples (there might be repeat modifiers
        # that return multiple patterns).
        values = [(1, pat, 0)]
        for modifier in modifiers:
            # We eventually flatten list of lists into a single list
            values = flatten([modifier(v) for v in values])
        return values

    def visit_euclid_modifier(self, node):
        k = self.eval(node["k"])
        n = self.eval(node["n"])
        rotation = self.eval(node["rotation"]) if "rotation" in node else pure(0)
        return k, n, rotation

    def visit_modifier(self, node):
        # This is a bit ugly, but we maintain the "state" of modifiers by returning
        # a tuple of 3 elements: (weight, pattern, degrade_ratio), where:
        #
        # * `weight` is the current weight value for timecat
        # * `pattern` is the modified pattern
        # * `degrade_ratio` is the accumulated degrade ratio.
        #
        # The return value of the modifier functions is a list of Patterns,
        # because the repeat modifier might return multiple patterns of the
        # element, so we generalize it into a list for all modifiers.
        if node["op"] == "degrade":
            # Use the formula `n / (n + 1)` to increase the degrade ratio
            # "linearly" We expect there is a single degrade modifier
            # (guaranteed by the AST), so we can use the `count` as the final
            # count of degrade occurrences.
            return lambda w_p: [
                (w_p[0], w_p[1], Fraction(node["count"], node["count"] + 1))
            ]
        elif node["op"] == "repeat":
            return lambda w_p: [w_p] * (node["count"] + 1)
        elif node["op"] == "fast":
            return lambda w_p: [(w_p[0], w_p[1].fast(node["value"]), w_p[2])]
        elif node["op"] == "slow":
            return lambda w_p: [(w_p[0], w_p[1].slow(node["value"]), w_p[2])]
        elif node["op"] == "weight":
            # Overwrite current weight state value with the new weight from this
            # modifier.
            return lambda w_p: [(node["value"], w_p[1], w_p[2])]
        return id

    def visit_number(self, node):
        return pure(node["value"])

    def visit_word(self, node):
        if node["index"]:
            return s(node["value"]) << n(node["index"])
        else:
            return pure(node["value"])

    def visit_rest(self, node):
        return silence()
