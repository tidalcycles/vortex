from parsimonious import NodeVisitor


class TidalVisitor(NodeVisitor):
    def generic_visit(self, node, visited_children):
        """The generic visit method."""
        return visited_children or node


visitor = TidalVisitor()
