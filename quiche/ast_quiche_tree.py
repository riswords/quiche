from typing import List, Optional
from ast import AST, Expr, Str, Name, fix_missing_locations

from astor import parse_file

from quiche.quiche_tree import QuicheTree
from quiche.insert_ast_block_traversal import InsertASTBlockTraversal


class ASTQuicheTree(QuicheTree):
    # NOTE: Prefer from_file() to from_ast(). If using from_ast(), you must
    # run ast.fix_missing_locations(InsertASTBlockTraversal().visit(ast_root))
    # on the AST before passing it to from_ast() to ensure that it has the
    # expected block structure.

    def __init__(self, root: AST = None):
        self.root: Optional[AST] = root
        self._children: List[ASTQuicheTree] = []
        if root is not None:
            self.from_ast(root)

    @staticmethod
    def parse_file(filename) -> AST:
        root = parse_file(filename)
        return fix_missing_locations(InsertASTBlockTraversal().visit(root))

    def from_file(self, filename) -> None:
        self.from_ast(ASTQuicheTree.parse_file(filename))

    def from_ast(self, tree: AST) -> None:
        self.root = tree
        self._children = []
        if hasattr(self.root, "_fields"):
            for field in self.root._fields:
                child = getattr(self.root, field)
                if isinstance(child, List):
                    self._children.extend([ASTQuicheTree(c) for c in child])
                else:
                    self._children.append(ASTQuicheTree(child))

    def value(self):
        return type(self.root).__name__

    def children(self):
        return self._children

    def is_pattern_symbol(self):
        """
        A pattern symbol is an AST.Expr containing an AST.Str or
        AST.Name (i.e., variable reference) that starts with "__quiche__",
        e.g., "__quiche__x".
        """
        if isinstance(self.root, Expr):
            if isinstance(self.root.value, Str):
                return self.root.value.s.startswith("__quiche__")
            elif isinstance(self.root.value, Name):
                return self.root.value.id.startswith("__quiche__")
        return False

    @staticmethod
    def make_rule(lhs, rhs):
        from ast import parse, fix_missing_locations
        from quiche.rewrite import Rule

        # assumes LHS and RHS are single expressions
        lhs_ast = parse(lhs, mode="single").body[0]
        rhs_ast = parse(rhs, mode="single").body[0]
        lhs_ast2 = fix_missing_locations(InsertASTBlockTraversal().visit(lhs_ast))
        rhs_ast2 = fix_missing_locations(InsertASTBlockTraversal().visit(rhs_ast))
        lhs_qt = ASTQuicheTree(lhs_ast2)
        rhs_qt = ASTQuicheTree(rhs_ast2)
        return Rule(lhs_qt, rhs_qt)
