from functools import reduce

from parsimonious import Grammar, NodeVisitor
from parsimonious.nodes import Node

from vortex.control import n, s
from vortex.pattern import (
    degrade,
    fast,
    fastcat,
    id,
    pure,
    reify,
    silence,
    slow,
    timecat,
)

grammar = Grammar(
    r"""
    start = ws? sequence ws?

    sequence = seq_term (ws? seq_term)*
    seq_term = term weight?

    # Terms
    term = term_value modifiers
    term_value = number / word_with_index / rest
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
    ws = ~"\s+"
    """
)


class SmallVisitor(NodeVisitor):
    def visit_start(self, _node, children):
        _, element, _ = children
        return element

    def visit_sequence(self, _node, children):
        seq_term, other_seq_terms = children
        if isinstance(other_seq_terms, Node):
            return reify(seq_term[1])
        other_seq_terms = [t for _, t in other_seq_terms]
        return timecat(seq_term, *other_seq_terms)

    def visit_seq_term(self, _node, children):
        term, weight = children
        if isinstance(weight, Node):
            return (1, term)
        return (weight[0], term)

    ##
    # Terms
    #

    def visit_term(self, _node, children):
        value, modifiers = children
        return modifiers(reify(value))

    def visit_term_value(self, _node, children):
        return children[0]

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

    def visit_modifier(self, _node, children):
        return children[0]

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


visitor = SmallVisitor()


def small(code, print_ast=False):
    tree = grammar.parse(code)
    if print_ast:
        print(tree.prettily())
    output = visitor.visit(tree)
    return output
