from abc import ABC, abstractmethod


class QuicheTree(ABC):
    @abstractmethod
    def value(self):
        pass

    @abstractmethod
    def children(self):
        pass

    @abstractmethod
    def is_pattern_symbol(self):
        pass

    def matches_enode(self, enode):
        if self.value() != enode.key:
            return False
        return True

    def __repr__(self) -> str:
        if self.children():
            return (
                f'({self.value()} {" ".join(str(child) for child in self.children())})'
            )
        else:
            return str(self.value())

    def _repr_svg_(self):
        from graphviz import Digraph

        def escape(x):
            escapes = [('|', '\\|'),
                       ('<', '\\<'),
                       ('>', '\\>')]
            x = str(x)
            for old, new in escapes:
                x = x.replace(old, new)
            # return str(x).replace('|', '\\|').replace('<', '\\<').replace('>', '\\>')
            return x

        def make_node(graph, x):
            node_id = str(id(x))
            if hasattr(x.value(), "__name__"):
                xvalue = x.value().__name__
            else:
                xvalue = x.value()
            graph.node(f'{node_id}', label=f'{escape(xvalue)}', shape='rectangle')
            node_children = x.children()
            if node_children:
                for child in node_children:
                    child_id = make_node(graph, child)
                    graph.edge(f'{node_id}', f'{child_id}')
            return node_id

        graph = Digraph(node_attr={'shape': 'record', 'height': '.1'})
        make_node(graph, self)
        return graph.pipe(format='svg', encoding='utf-8')

    def write_to_svg(self, filename):
        """
        Write QuicheTree to file in SVG format.

        :param filename: filename to write
        :return: None
        """
        with open(filename, "w") as f:
            f.write(self._repr_svg_())
