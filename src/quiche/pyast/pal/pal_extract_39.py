from quiche.pyast.pal.pal_block import TypeIgnoreBlock

from quiche.pyast.pal.pal_extractor import PALExtractor


class PALExtract39(PALExtractor):
    def visit_TypeIgnoreBlock(self, node: TypeIgnoreBlock):
        self.generic_visit(node)
        return node.body
