from parsimonious import NodeVisitor, Grammar
from vortex.pattern import pure, fastcat

grammar = Grammar(
    r"""
    start = ws? term ws?

    term = (number / word) modifier?

    # Terms
    word = ~r"[-\w]+"
    number = real / integer

    # Modifiers
    modifier = fast / slow / replicate / random / elongate / sample_select
    fast = '*' number
    slow = '/' number
    replicate = '!'
    random = '?'
    elongate = '@' number
    sample_select = ':' number

    # Numbers
    real = integer '.' pos_integer?
    integer = minus? pos_integer
    pos_integer = !minus ~r"[0-9]+"

    # Others
    minus = '-'
    ws = ~"\s*"
    """
)


class SmallVisitor(NodeVisitor):
    def visit_start(self, node, visited_children):
        _, element, _ = visited_children
        return element

    def visit_term(self, node, visited_children):
        term, modifier = visited_children
        pat = pure(term)
        if not isinstance(modifier, dict):
            return pat
        else:
            value = modifier.get("value")
            if modifier["type"] == "fast":
                return pat.fast(value)
            elif modifier["type"] == "slow":
                return pat.slow(value)
            elif modifier["type"] == "replicate":
                return pat
            elif modifier["type"] == "random":
                return pat
            else:
                raise NotImplementedError(f"unknown modifier type: {modifier['type']}")

    def visit_fast(self, node, visited_children):
        _, number = visited_children
        return {"type": "fast", "value": number}

    def visit_word(self, node, visited_children):
        return node.text

    def visit_real(self, node, visited_children):
        return float(node.text)

    def visit_integer(self, node, visited_children):
        return int(node.text)

    def visit_pos_integer(self, node, visited_children):
        return int(node.text)

    def visit_ws(self, node, visited_children):
        return

    def generic_visit(self, node, visited_children):
        """The generic visit method."""
        return (visited_children and visited_children[0]) or node


visitor = SmallVisitor()


def small(code, print_ast=False):
    tree = grammar.parse(code)
    if print_ast:
        print(tree.prettily())
    output = visitor.visit(tree)
    return output
