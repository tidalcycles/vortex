from parsimonious import NodeVisitor
from vortex.pattern import pure, fastcat


class TidalVisitor(NodeVisitor):
    def visit_start(self, node, visited_children):
        _, element, _ = visited_children
        return element[0]

    def visit_sequence(self, node, visited_children):
        first_elem, other_elems = visited_children
        other_elems = [elem[0] for _, elem in other_elems]
        return fastcat(first_elem, *other_elems)

    def visit_element(self, node, visited_children):
        return pure(node.text)

    def generic_visit(self, node, visited_children):
        """The generic visit method."""
        return visited_children or node


visitor = TidalVisitor()
