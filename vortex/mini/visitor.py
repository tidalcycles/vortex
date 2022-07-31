from parsimonious import NodeVisitor

from vortex.pattern import fastcat, pure


class TidalVisitor(NodeVisitor):
    def visit_start(self, node, visited_children):
        _, element, _ = visited_children
        return element[0]

    def visit_element(self, node, visited_children):
        return pure(node.text)

    def visit_sequence(self, node, visited_children):
        first_elem, other_elems = visited_children
        other_elems = [elem[0] for _, elem in other_elems]
        return fastcat(first_elem, *other_elems)

    def visit_basic_modifier(self, node, visited_children):
        return visited_children[0]

    def visit_slow(self, node, visited_children):
        _, scalar = visited_children
        return {"type": "slow", "value": scalar}

    def visit_number(self, node, visited_children):
        return visited_children[0]

    def visit_float(self, node, visited_children):
        return float(node.text)

    def visit_integer(self, node, visited_children):
        return int(node.text)

    def generic_visit(self, node, visited_children):
        """The generic visit method."""
        return visited_children or node


visitor = TidalVisitor()
