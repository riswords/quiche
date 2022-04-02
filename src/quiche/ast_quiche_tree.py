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
        self._is_pattern_symbol: bool = False
        if src_file is not None:
            self.from_file(src_file)
            if root is not None:
                print("WARNING [ASTQuicheTree]: source file and AST are both specified. Ignoring AST.")
        elif root is not None:
            self.from_ast(root)

        self.__init_pattern_symbol()

    @staticmethod
    def parse_file(filename) -> AST:
        root = parse_file(filename)
        return fix_missing_locations(InsertASTBlockTraversal().visit(root))

    def from_file(self, filename) -> None:
        self.from_ast(ASTQuicheTree.parse_file(filename))

    def from_ast(self, tree: AST) -> None:
        self.root = tree
        self._children = []
        if not ASTQuicheTree.is_primitive_type(type(self.root)):
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
        # Primitive wrappers (e.g., Str, Name)
        if ASTQuicheTree.is_primitive_type(root_type):
            children = [root_type]
            if hasattr(self.root, "_fields"):
                for field in self.root._fields:
                    if hasattr(self.root, field):
                        children.append(getattr(self.root, field))
            return tuple(children)
        # identifiers
        elif root_type is str:
            return self.root
        else:
            return root_type

    def children(self):
        return self._children

    def __init_pattern_symbol(self):
        """
        Checks whether the root of this ASTQuicheTree is a pattern
        symbol and caches to self._is_pattern_symbol.

        A pattern symbol is one of:
            - AST string or variable prefixed with "__quiche__" (i.e.,
                an AST.Expr containing an AST.Str or AST.Name)
            - A QuicheBlock with a single child that is a pattern symbol (this
            allows us to match a body with one or more expressions)
        """
        if isinstance(self.root, Expr):
            if isinstance(self.root.value, Str):
                self._is_pattern_symbol = self.root.value.s.startswith("__quiche__")
            elif isinstance(self.root.value, Name):
                self._is_pattern_symbol = self.root.value.id.startswith("__quiche__")
        elif isinstance(self.root, QuicheBlock) and len(self.children()) == 1:
            self._is_pattern_symbol = self.children()[0].is_pattern_symbol()
        return

    def is_pattern_symbol(self) -> bool:
        """
        Indicates whether the root of the ASTQuicheTree is a pattern
        symbol. (See __init_pattern_symbol() for implementation details.)
        """
        return self._is_pattern_symbol

    @staticmethod
    def is_primitive_type(node_type):
        return node_type in [ast.Num, ast.Str, ast.Bytes, ast.NameConstant, ast.Name]

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
        def is_leaf(node_type):
            return node_type in [
                ast.Load, ast.Store, ast.Del, ast.AugLoad, ast.AugStore,
                ast.Param, ast.And, ast.Or, ast.Add, ast.Sub, ast.Mult,
                ast.MatMult, ast.Div, ast.Mod, ast.Pow, ast.LShift, ast.RShift,
                ast.BitOr, ast.BitXor, ast.BitAnd, ast.FloorDiv, ast.Invert,
                ast.Not, ast.UAdd, ast.USub, ast.Eq, ast.NotEq, ast.Lt,
                ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn]
        # identifiers
        if type(node_type) is str:
            return ASTQuicheTree(root=node_type)
        # primitive wrappers (e.g., Str, Name)
        elif type(node_type) is tuple:
            ast_type = node_type[0]
            args = node_type[1:]
            return ASTQuicheTree(root=ast_type(*args))
        # none type
        elif issubclass(node_type, type(None)):
            return ASTQuicheTree(root=None)
        # QuicheBlocks
        elif issubclass(node_type, QuicheBlock):
            child_roots = [c.root for c in children]
            return ASTQuicheTree(root=node_type(child_roots))
        # Already wrapped in a QuicheTree
        elif isinstance(node_type, ASTQuicheTree):
            return node_type
        else:
            if children:
                args = tuple([c.root for c in children])
                return ASTQuicheTree(root=node_type(*args))
            elif is_leaf(node_type):
                # node_type with no children
                return ASTQuicheTree(root=node_type())
            else:
                # node type with one child: None
                return ASTQuicheTree(root=node_type(None))

    def to_source_string(self):
        rem_blocks = fix_missing_locations(RemoveASTBlockTraversal().visit(self.root))
        return to_source(rem_blocks)

    def to_file(self, filename):
        with open(filename, "w") as f:
            f.write(self.to_source_string())
