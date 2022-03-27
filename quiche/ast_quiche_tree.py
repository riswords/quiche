import ast
from typing import List, Optional
from ast import AST, Expr, Str, Name, fix_missing_locations

from astor import parse_file, to_source

from quiche.quiche_tree import QuicheTree
from quiche.insert_ast_block_traversal import InsertASTBlockTraversal, QuicheBlock, RemoveASTBlockTraversal


class ASTQuicheTree(QuicheTree):
    # NOTE: Prefer from_file() to from_ast(). If using from_ast(), you must
    # run ast.fix_missing_locations(InsertASTBlockTraversal().visit(ast_root))
    # on the AST before passing it to from_ast() to ensure that it has the
    # expected block structure.

    def __init__(self, src_file: str = None, root: AST = None):
        self.root: Optional[AST] = root
        self._children: List[ASTQuicheTree] = []
        if src_file is not None:
            self.from_file(src_file)
            if root is not None:
                print("WARNING [ASTQuicheTree]: source file and AST are both specified. Ignoring AST.")
        elif root is not None:
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
                if hasattr(self.root, field):
                    child = getattr(self.root, field)
                    if isinstance(child, List):
                        self._children.extend([ASTQuicheTree(root=c) for c in child])
                    else:
                        self._children.append(ASTQuicheTree(root=child))
                else:
                    self._children.append(ASTQuicheTree(root=None))

    def value(self):
        root_type = type(self.root)
        if self.root is None or root_type in (str, int, bool, float):
            return self.root
        else:
            return root_type

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
        lhs_qt = ASTQuicheTree(root=lhs_ast2)
        rhs_qt = ASTQuicheTree(root=rhs_ast2)
        return Rule(lhs_qt, rhs_qt)

    @staticmethod
    # TODO: This is kind of a mess - we should definitely clean this up...
    def make_node(node_type, children: List["ASTQuicheTree"]) -> "ASTQuicheTree":
        if node_type is type(None) or node_type is None:
            return ASTQuicheTree(root=None)
        elif type(node_type) in [str, int, bool, float]:
            print("MAKING NODE OF TYPE: {} WITH ROOT: {}".format(type(node_type), node_type))
            return ASTQuicheTree(root=node_type)
        elif issubclass(node_type, QuicheBlock):
            child_roots = [c.root for c in children]
            return ASTQuicheTree(root=node_type(child_roots))
        elif isinstance(node_type, ASTQuicheTree):
            return node_type
        else:
            if children:
                args = [c.root for c in children]
                if node_type in [ast.Num]:
                    print("MAKING NODE OF TYPE: {} WITH ARGS: {}, CHILD VAL: {}".format(node_type, args, children[0].value()))
                return ASTQuicheTree(root=node_type(*args))
            elif node_type in [ast.Load, ast.Store, ast.Del, ast.AugLoad, ast.AugStore, ast.Param,
                    ast.And, ast.Or, ast.Add, ast.Sub, ast.Mult, ast.MatMult, ast.Div, ast.Mod,
                    ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv,
                    ast.Invert, ast.Not, ast.UAdd, ast.USub,
                    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn]:
                return ASTQuicheTree(root=node_type())
            else:
                return ASTQuicheTree(root=node_type(None))

    def to_source_string(self):
        rem_blocks = fix_missing_locations(RemoveASTBlockTraversal().visit(self.root))
        return to_source(rem_blocks)

    def to_file(self, filename):
        with open(filename, "w") as f:
            source = self.to_source_string()
            f.write(to_source(source))
