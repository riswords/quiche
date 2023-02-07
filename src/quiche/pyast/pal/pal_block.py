from sys import version_info
from typing import Sequence, Optional, TypeVar, Generic, Callable, Tuple, Any

import ast

from ast import (
    AST,
    NodeTransformer,
    stmt,
    expr,
    keyword,
    withitem,
    excepthandler,
    alias,
    comprehension,
    cmpop,
    slice,
    arg,
)


class PAL:
    lifter: NodeTransformer
    extractor: NodeTransformer

    def __init__(self) -> None:
        self.lifter = PALLift().make_lifter()
        self.extractor = PALExtract().make_extractor()

    def is_leaf_node(self, node: AST) -> bool:
        return hasattr(node, "_fields") and len(node._fields) == 0

    # NOTE: Might need to adjust for different Python versions
    def is_leaf_node_type(self, node_type: type) -> bool:
        return node_type in [
            ast.Load,
            ast.Store,
            ast.Del,
            ast.AugLoad,
            ast.AugStore,
            ast.Param,
            ast.And,
            ast.Or,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.MatMult,
            ast.Div,
            ast.Mod,
            ast.Pow,
            ast.LShift,
            ast.RShift,
            ast.BitOr,
            ast.BitXor,
            ast.BitAnd,
            ast.FloorDiv,
            ast.Invert,
            ast.Not,
            ast.UAdd,
            ast.USub,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Is,
            ast.IsNot,
            ast.In,
            ast.NotIn,
        ]


class PALLift:
    lifter: Optional[NodeTransformer]

    def __init__(self, lifter: Optional[NodeTransformer] = None):
        self.lifter = lifter

    def make_lifter(self) -> NodeTransformer:
        if self.lifter is None:
            ver_tup = version_info[:2]
            # print("PYTHON VERSION: ", ver_tup)
            if ver_tup == (3, 7):
                from .pal_lift_37 import PALLift37

                self.lifter = PALLift37()
            elif ver_tup == (3, 8):
                from .pal_lift_38 import PALLift38

                self.lifter = PALLift38()
            elif ver_tup == (3, 9):
                from .pal_lift_39 import PALLift39

                self.lifter = PALLift39()
            elif ver_tup == (3, 10):
                from .pal_lift_310 import PALLift310

                self.lifter = PALLift310()
            else:
                raise ValueError(f"Unsupported Python version: {ver_tup}")
        return self.lifter


class PALExtract:
    extractor: Optional[NodeTransformer]

    def __init__(self, extractor: Optional[NodeTransformer] = None):
        self.extractor = extractor

    def make_extractor(self):
        if self.extractor is None:
            ver_tup = version_info[:2]
            if ver_tup == (3, 7):
                from .pal_extract_37 import PALExtract37

                self.extractor = PALExtract37()
            elif ver_tup == (3, 8):
                from .pal_extract_38 import PALExtract38

                self.extractor = PALExtract38()
            elif ver_tup == (3, 9):
                from .pal_extract_39 import PALExtract39

                self.extractor = PALExtract39()
            elif ver_tup == (3, 10):
                from .pal_extract_310 import PALExtract310

                self.extractor = PALExtract310()
            else:
                raise ValueError(f"Unsupported Python version: {ver_tup}")
        return self.extractor


class PALNode(AST):
    pass


# GENERIC BLOCK TYPE
B = TypeVar("B")


class PALBlock(Generic[B], PALNode):
    body: Sequence[B]
    _fields = ("body",)

    def __init__(self, body: Sequence[B]):
        self.body = body


# WRAPPERS FOR BUILTIN TYPES
T = TypeVar("T")


class PALPrimitive(Generic[T], PALNode):
    _fields = ("value",)

    def __init__(self, value: T):
        self.value = value


class PALLeaf(Generic[T], PALNode):
    _fields = (
        "kind",
        "constr",
        "args",
    )

    def __init__(self, kind: str, constr: Callable[[T], Any], *args: T):
        self.kind: Optional[str] = kind
        self.constr: Callable[[T], Any] = constr
        self.args: Tuple[T, ...] = args


class PALIdentifier(PALPrimitive[Optional[str]]):
    def __init__(self, ident: Optional[str] = None):
        super().__init__(ident)


class IdentifierBlock(PALBlock[PALIdentifier]):
    def __init__(self, idents: Sequence[PALIdentifier]) -> None:
        super().__init__(idents)


# BLOCK TYPES
class StmtBlock(PALBlock[stmt]):
    def __init__(self, body: Sequence[stmt]) -> None:
        super().__init__(body)


class ExprBlock(PALBlock[Optional[expr]]):
    def __init__(self, exprs: Sequence[Optional[expr]]) -> None:
        super().__init__(exprs)


class SliceBlock(PALBlock[slice]):
    def __init__(self, slices: Sequence[slice]):
        super().__init__(slices)


class CmpopBlock(PALBlock[cmpop]):
    def __init__(self, ops: Sequence[cmpop]):
        super().__init__(ops)


class ComprehensionBlock(PALBlock[comprehension]):
    def __init__(self, comprehensions: Sequence[comprehension]):
        super().__init__(comprehensions)


class ExceptHandlerBlock(PALBlock[excepthandler]):
    def __init__(self, handlers: Sequence[excepthandler]) -> None:
        super().__init__(handlers)


class ArgBlock(PALBlock[arg]):
    def __init__(self, args: Sequence[arg]):
        super().__init__(args)


class KeywordBlock(PALBlock[keyword]):
    def __init__(self, keywords: Sequence[keyword]) -> None:
        super().__init__(keywords)


class AliasBlock(PALBlock[alias]):
    def __init__(self, aliases: Sequence[alias]) -> None:
        super().__init__(aliases)


class WithItemBlock(PALBlock[withitem]):
    def __init__(self, items: Sequence[withitem]) -> None:
        super().__init__(items)


if version_info[:2] >= (3, 8):
    from ast import type_ignore

    class TypeIgnoreBlock(PALBlock[type_ignore]):
        def __init__(self, type_ignores: Sequence[type_ignore]) -> None:
            super().__init__(type_ignores)


if version_info[:2] >= (3, 10):
    from ast import match_case, pattern

    class MatchCaseBlock(PALBlock[match_case]):
        def __init__(self, cases: Sequence[match_case]) -> None:
            super().__init__(cases)

    class PatternBlock(PALBlock[pattern]):
        def __init__(self, patterns: Sequence[pattern]) -> None:
            super().__init__(patterns)
