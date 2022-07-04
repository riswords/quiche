from typing import List, Optional, Tuple
from ast import AST, Expr, Str, Name, fix_missing_locations, Constant, parse

from astor import parse_file, to_source

from quiche.quiche_tree import QuicheTree
from quiche.pyast.pal.pal_block import PAL, PALBlock, PALLift, PALLeaf


class ASTQuicheTree(QuicheTree):
    # NOTE: Prefer from_file() to from_ast(). If using from_ast(), you must
    # run ast.fix_missing_locations(InsertASTBlockTraversal().visit(ast_root))
    # on the AST before passing it to from_ast() to ensure that it has the
    # expected block structure.
    pal = PAL()

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
    def parse_string(source_string: str) -> AST:
        root = parse(source_string)
        return fix_missing_locations(PALLift().make_lifter().visit(root))

    @staticmethod
    def parse_file(filename) -> AST:
        root = parse_file(filename)
        return fix_missing_locations(PALLift().make_lifter().visit(root))

    def from_file(self, filename) -> None:
        self.from_ast(ASTQuicheTree.parse_file(filename))

    def from_ast(self, tree: AST) -> None:
        self.root = tree
        self._children = []
        if not ASTQuicheTree.is_primitive_type(type(self.root)):
            for field in getattr(self.root, "_fields", []):
                child = getattr(self.root, field, None)
                if isinstance(child, List):
                    if len(self.root._fields) != 1:
                        print("BAD LIST FLATTENING: {}".format(child))
                    self._children.extend([ASTQuicheTree(root=c) for c in child])
                else:
                    self._children.append(ASTQuicheTree(root=child))

    def value(self):
        root_type = type(self.root)
        # Primitive wrappers (e.g., Str, Name)
        if ASTQuicheTree.is_primitive_type(root_type):
            return (self.root.kind, self.root.constr, *self.root.args)
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
        if isinstance(self.root, PALLeaf):
            if self.root.constr in [Str, Name]:
                self._is_pattern_symbol = self.root.args[0].startswith("__quiche__")
            elif self.root.constr is Constant and self.root.kind == "str":
                self._is_pattern_symbol = self.root.args[0].startswith("__quiche__")
        elif isinstance(self.root, Expr):
            self._is_pattern_symbol = self.children()[0].is_pattern_symbol()
        elif isinstance(self.root, PALBlock) and len(self.children()) == 1:
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
        return node_type is PALLeaf

    @staticmethod
    def make_rule(lhs, rhs):
        from ast import parse, fix_missing_locations
        from quiche.rewrite import Rule

        # assumes LHS and RHS are single expressions or statements
        lhs_ast = parse(lhs, mode="single").body[0]
        rhs_ast = parse(rhs, mode="single").body[0]
        if isinstance(lhs_ast, Expr):
            lhs_ast = lhs_ast.value
        if isinstance(rhs_ast, Expr):
            rhs_ast = rhs_ast.value
        lifter = PALLift().make_lifter()
        lhs_ast2 = fix_missing_locations(lifter.visit(lhs_ast))
        rhs_ast2 = fix_missing_locations(lifter.visit(rhs_ast))
        lhs_qt = ASTQuicheTree(root=lhs_ast2)
        rhs_qt = ASTQuicheTree(root=rhs_ast2)
        return Rule(lhs_qt, rhs_qt)

    @staticmethod
    # TODO: This is kind of a mess - we should definitely clean this up...
    def make_node(node_type, children: Tuple["ASTQuicheTree", ...]) -> "ASTQuicheTree":
        # identifiers
        if type(node_type) is str:
            return ASTQuicheTree(root=node_type)
        # primitive wrappers (e.g., Str, Name)
        elif type(node_type) is tuple:
            ast_type = node_type[1]
            args = node_type[2:]
            return ASTQuicheTree(root=ast_type(*args))
        # none type
        elif issubclass(node_type, type(None)):
            return ASTQuicheTree(root=None)
        # PAL Blocks
        elif issubclass(node_type, PALBlock):
            child_roots = [c.root for c in children]
            return ASTQuicheTree(root=node_type(child_roots))
        # Already wrapped in a QuicheTree
        elif isinstance(node_type, ASTQuicheTree):
            return node_type
        else:
            if children:
                args = tuple([c.root for c in children])
                return ASTQuicheTree(root=node_type(*args))
            elif ASTQuicheTree.pal.is_leaf_node(node_type):
                # node_type with no children
                return ASTQuicheTree(root=node_type())
            else:
                # node type with one child: None
                return ASTQuicheTree(root=node_type(None))

    def to_source_string(self):
        rem_blocks = fix_missing_locations(ASTQuicheTree.pal.extractor.visit(self.root))
        return to_source(rem_blocks)

    def to_file(self, filename):
        with open(filename, "w") as f:
            f.write(self.to_source_string())
