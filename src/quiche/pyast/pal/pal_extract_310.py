from ast import NodeTransformer

from quiche.pyast.pal.pal_block import (
    IdentifierBlock,
    PALIdentifier,
    PALPrimitive,
    StmtBlock,
    ExprBlock,
    SliceBlock,
    CmpopBlock,
    ComprehensionBlock,
    ExceptHandlerBlock,
    ArgBlock,
    KeywordBlock,
    AliasBlock,
    WithItemBlock,
)


class PALExtract310(NodeTransformer):
    def visit_StmtBlock(self, node: StmtBlock):
        self.generic_visit(node)
        return node.body

    def visit_ExprBlock(self, node: ExprBlock):
        self.generic_visit(node)
        return node.body

    def visit_KeywordBlock(self, node: KeywordBlock):
        self.generic_visit(node)
        return node.body

    def visit_WithItemBlock(self, node: WithItemBlock):
        self.generic_visit(node)
        return node.body

    def visit_ExceptHandlerBlock(self, node: ExceptHandlerBlock):
        self.generic_visit(node)
        return node.body

    def visit_AliasBlock(self, node: AliasBlock):
        self.generic_visit(node)
        return node.body

    def visit_ComprehensionBlock(self, node: ComprehensionBlock):
        self.generic_visit(node)
        return node.body

    def visit_CmpopBlock(self, node: CmpopBlock):
        self.generic_visit(node)
        return node.body

    def visit_SliceBlock(self, node: SliceBlock):
        self.generic_visit(node)
        return node.body

    def visit_ArgBlock(self, node: ArgBlock):
        self.generic_visit(node)
        return node.body

    def visit_IdentifierBlock(self, node: IdentifierBlock):
        # don't use generic_visit because it doesn't handle PALIdentifier
        # changing from AST to str correctly (it explodes the string into a
        # list of chars because when a value changes from AST to non-AST, it
        # uses `extend` not `append` to combine)
        return [self.visit(ident) for ident in node.body]

    def visit_PALPrimitive(self, node: PALPrimitive):
        return node.value

    def visit_PALIdentifier(self, node: PALIdentifier):
        return node.value
