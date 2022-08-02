from functools import reduce

from parsimonious import Grammar, NodeVisitor
from parsimonious.nodes import Node

from vortex.control import n, s
from vortex.pattern import degrade, fast, fastcat, id, pure, reify, silence, slow

grammar = Grammar(
    r"""
    start = ws? term ws?

    # Terms
    term = (number / rest / word_with_index) weight? modifiers
    word_with_index = word index?
    weight = '@' number
    index = ':' number

    # Term modifiers
    modifiers = modifier*
    modifier = fast / slow / repeat / degrade
    fast = '*' number
    slow = '/' number
    repeat = '!'+
    degrade = '?'+

    # Primitives
    word = ~r"[-\w]+"
    rest = '~'
    number = real / integer
    real = integer '.' pos_integer?
    integer = minus? pos_integer
    pos_integer = !minus ~r"[0-9]+"

    # Misc
    minus = '-'
    ws = ~"\s*"
    """
)


class SmallVisitor(NodeVisitor):
    def visit_start(self, _node, children):
        _, element, _ = children
        return element

    ##
    # Terms
    #

    def visit_term(self, _node, children):
        term, weight, modifiers = children
        pat = modifiers(reify(term))
        if isinstance(weight, Node):
            return pat
        return {"type": "term", "value": pat, "weight": weight}

    def visit_rest(self, _node, _children):
        return silence()

    def visit_word_with_index(self, _node, children):
        word, index = children
        if isinstance(index, Node):
            return pure(word)
        return s(word) << n(index)

    def visit_index(self, _node, children):
        _, number = children
        return number

    def visit_weight(self, _node, children):
        _, number = children
        return number

    ##
    # Modifiers
    #

    def visit_modifiers(self, _node, children):
        if children:
            return lambda pat: reduce(lambda p, func: func(p), children, pat)
        return id

    def visit_fast(self, _node, children):
        _, number = children
        return fast(number)

    def visit_slow(self, _node, children):
        _, number = children
        return slow(number)

    def visit_repeat(self, _node, children):
        n = len(children)
        return lambda pat: fastcat(pat, *[pat for _ in range(n)])

    def visit_degrade(self, _node, children):
        n = len(children)
        return lambda pat: reduce(lambda p, _: degrade(p), range(n), pat)

    ##
    # Primitives
    #

    def visit_word(self, node, _children):
        return node.text

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
        """The generic visit method."""
        if children and len(children) > 1:
            raise ValueError(
                (
                    "Using generic_visit but there were multiple visited children. "
                    "Please define a proper visit method for this node"
                )
            )
        return (children and children[0]) or node


visitor = SmallVisitor()


def small(code, print_ast=False):
    tree = grammar.parse(code)
    if print_ast:
        print(tree.prettily())
    output = visitor.visit(tree)
    return output
