from quiche.pyast.pal.pal_block import (
    TypeIgnoreBlock,
    MatchCaseBlock,
    PatternBlock,
)

from quiche.pyast.pal.pal_extractor import PALExtractor


class PALExtract310(PALExtractor):
    def visit_TypeIgnoreBlock(self, node: TypeIgnoreBlock):
        self.generic_visit(node)
        return node.body

    def visit_MatchCaseBlock(self, node: MatchCaseBlock):
        self.generic_visit(node)
        return node.body

    def visit_PatternBlock(self, node: PatternBlock):
        self.generic_visit(node)
        return node.body
