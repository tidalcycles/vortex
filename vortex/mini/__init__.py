from .grammar import grammar
from .visitor import visitor


def mini(code: str):
    tree = grammar.parse(code)
    output = visitor.visit(tree)
    return output
