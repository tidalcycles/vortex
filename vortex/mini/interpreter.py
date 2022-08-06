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
        value, modifiers = children
        return dict(type="element", value=value, modifiers=modifiers)

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
        for es in elements:
            weight = es[0][0] if es else 1
            deg_by = es[0][2] if es else 0
            tc_args.append(
                (len(es) * weight, sequence(*[e[1] for e in es]).degrade_by(deg_by))
            )
        return timecat(*tc_args)

    def visit_polyrhythm(self, node):
        return polyrhythm(*[self.eval(seq) for seq in node["seqs"]])

    def visit_polymeter(self, node):
        return polymeter(*[self.eval(seq) for seq in node["seqs"]], steps=node["steps"])

    def visit_element(self, node):
        modifiers = [self.eval(m) for m in node["modifiers"]]
        values = [(1, self.eval(node["value"]), 0)]
        for modifier in modifiers:
            values = flatten([modifier(v) for v in values])
        return values

    def visit_modifier(self, node):
        if node["op"] == "degrade":
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
