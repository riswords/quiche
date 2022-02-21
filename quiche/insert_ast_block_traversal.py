from typing import Sequence, List
from abc import ABC

from ast import (
    AST,
    NodeTransformer,
    Module,
    Interactive,
    Suite,
    FunctionDef,
    AsyncFunctionDef,
    ClassDef,
    Delete,
    Assign,
    For,
    AsyncFor,
    While,
    If,
    With,
    AsyncWith,
    Try,
    Import,
    ImportFrom,
    Global,
    Nonlocal,
    BoolOp,
    Dict as DictAST,
    Set as SetAST,
    ListComp,
    SetComp,
    DictComp,
    GeneratorExp,
    Compare,
    Call,
    JoinedStr,
    List as ListAST,
    Tuple as TupleAST,
    ExtSlice,
    arguments,
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


class QuicheBlock(ABC):
    body: Sequence[AST]


class StmtSequence(stmt, QuicheBlock):
    _fields = ("body",)

    def __init__(self, stmts: List[stmt]):
        self.body = stmts


class ExprSequence(expr, QuicheBlock):
    _fields = ("body",)

    def __init__(self, exprs: List[expr]):
        self.body = exprs


class KeywordSequence(keyword, QuicheBlock):
    _fields = ("body",)

    def __init__(self, keywords: List[keyword]):
        self.body = keywords


class WithItemSequence(withitem, QuicheBlock):
    _fields = ("body",)

    def __init__(self, withitems: List[withitem]):
        self.body = withitems


class ExceptHandlerSequence(excepthandler, QuicheBlock):
    _fields = ("body",)

    def __init__(self, handlers: List[excepthandler]):
        self.body = handlers


class AliasSequence(alias, QuicheBlock):
    _fields = ("body",)

    def __init__(self, aliases: List[alias]):
        super().__init__()
        self.body = aliases


class ComprehensionSequence(comprehension, QuicheBlock):
    _fields = ("body",)

    def __init__(self, comprehensions: List[comprehension]):
        self.body = comprehensions


class CmpOpSequence(cmpop, QuicheBlock):
    _fields = ("body",)

    def __init__(self, cmpops: List[cmpop]):
        self.body = cmpops


class SliceSequence(slice, QuicheBlock):
    _fields = ("body",)

    def __init__(self, slices: List[slice]):
        self.body = slices


class ArgSequence(arg, QuicheBlock):
    _fields = ("body",)

    def __init__(self, args: List[arg]):
        self.body = args


class IdentifierSequence(AST, QuicheBlock):
    _fields = ("ids",)

    def __init__(self, ids: List[str]):
        self.ids: List[str] = ids


class InsertASTBlockTraversal(NodeTransformer):
    def visit_Module(self, node: Module) -> Module:
        # Short-circuit: assume if the body is a StmtSequence, it's already
        # been transformed. NOTE: may need to revisit this later if this
        # transform is applied to fix-up after other modifications.
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return Module(body=StmtSequence(node.body))

    def visit_Interactive(self, node: Interactive) -> Interactive:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return Interactive(body=StmtSequence(node.body))

    def visit_Suite(self, node: Suite) -> Suite:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return Suite(body=StmtSequence(node.body))

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return FunctionDef(
            name=node.name,
            args=node.args,
            body=StmtSequence(node.body),
            decorator_list=ExprSequence(node.decorator_list),
            returns=node.returns,
        )

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> AsyncFunctionDef:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return AsyncFunctionDef(
            name=node.name,
            args=node.args,
            body=StmtSequence(node.body),
            decorator_list=ExprSequence(node.decorator_list),
            returns=node.returns,
        )

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        if isinstance(node.bases, ExprSequence):
            return node
        self.generic_visit(node)
        return ClassDef(
            name=node.name,
            bases=ExprSequence(node.bases),
            keywords=KeywordSequence(node.keywords),
            body=StmtSequence(node.body),
            decorator_list=ExprSequence(node.decorator_list),
        )

    def visit_Delete(self, node: Delete) -> Delete:
        if isinstance(node.targets, ExprSequence):
            return node
        self.generic_visit(node)
        return Delete(targets=ExprSequence(node.targets))

    def visit_Assign(self, node: Assign) -> Assign:
        if isinstance(node.targets, ExprSequence):
            return node
        self.generic_visit(node)
        return Assign(targets=ExprSequence(node.targets), value=node.value)

    def visit_For(self, node: For) -> For:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return For(
            target=node.target,
            iter=node.iter,
            body=StmtSequence(node.body),
            orelse=StmtSequence(node.orelse),
        )

    def visit_AsyncFor(self, node: AsyncFor) -> AsyncFor:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return AsyncFor(
            target=node.target,
            iter=node.iter,
            body=StmtSequence(node.body),
            orelse=StmtSequence(node.orelse),
        )

    def visit_While(self, node: While) -> While:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return While(
            test=node.test,
            body=StmtSequence(node.body),
            orelse=StmtSequence(node.orelse),
        )

    def visit_If(self, node: If) -> If:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return If(
            test=node.test,
            body=StmtSequence(node.body),
            orelse=StmtSequence(node.orelse),
        )

    def visit_With(self, node: With) -> With:
        if isinstance(node.items, WithItemSequence):
            return node
        self.generic_visit(node)
        return With(items=WithItemSequence(node.items), body=StmtSequence(node.body))

    def visit_AsyncWith(self, node: AsyncWith) -> AsyncWith:
        if isinstance(node.items, WithItemSequence):
            return node
        self.generic_visit(node)
        return AsyncWith(
            items=WithItemSequence(node.items), body=StmtSequence(node.body)
        )

    def visit_Try(self, node: Try) -> Try:
        if isinstance(node.body, StmtSequence):
            return node
        self.generic_visit(node)
        return Try(
            body=StmtSequence(node.body),
            handlers=ExceptHandlerSequence(node.handlers),
            orelse=StmtSequence(node.orelse),
            finalbody=StmtSequence(node.finalbody),
        )

    def visit_Import(self, node: Import) -> Import:
        if isinstance(node.names, AliasSequence):
            return node
        self.generic_visit(node)
        return Import(names=AliasSequence(node.names))

    def visit_ImportFrom(self, node: ImportFrom) -> ImportFrom:
        if isinstance(node.names, AliasSequence):
            return node
        self.generic_visit(node)
        return ImportFrom(
            module=node.module, names=AliasSequence(node.names), level=node.level
        )

    def visit_Global(self, node: Global) -> Global:
        if isinstance(node.names, IdentifierSequence):
            return node
        self.generic_visit(node)
        return Global(names=IdentifierSequence(node.names))

    def visit_Nonlocal(self, node: Nonlocal) -> Nonlocal:
        if isinstance(node.names, IdentifierSequence):
            return node
        self.generic_visit(node)
        return Nonlocal(names=IdentifierSequence(node.names))

    def visit_BoolOp(self, node: BoolOp) -> BoolOp:
        if isinstance(node.values, ExprSequence):
            return node
        self.generic_visit(node)
        return BoolOp(op=node.op, values=ExprSequence(node.values))

    def visit_Dict(self, node: DictAST) -> DictAST:
        if isinstance(node.keys, ExprSequence):
            return node
        self.generic_visit(node)
        return DictAST(keys=ExprSequence(node.keys), values=ExprSequence(node.values))

    def visit_Set(self, node: SetAST) -> SetAST:
        if isinstance(node.elts, ExprSequence):
            return node
        self.generic_visit(node)
        return SetAST(elts=ExprSequence(node.elts))

    def visit_ListComp(self, node: ListComp) -> ListComp:
        if isinstance(node.generators, ComprehensionSequence):
            return node
        self.generic_visit(node)
        return ListComp(elt=node.elt, generators=ComprehensionSequence(node.generators))

    def visit_SetComp(self, node: SetComp) -> SetComp:
        if isinstance(node.generators, ComprehensionSequence):
            return node
        self.generic_visit(node)
        return SetComp(elt=node.elt, generators=ComprehensionSequence(node.generators))

    def visit_DictComp(self, node: DictComp) -> DictComp:
        if isinstance(node.generators, ComprehensionSequence):
            return node
        self.generic_visit(node)
        return DictComp(
            key=node.key,
            value=node.value,
            generators=ComprehensionSequence(node.generators),
        )

    def visit_GeneratorExp(self, node: GeneratorExp) -> GeneratorExp:
        if isinstance(node.generators, ComprehensionSequence):
            return node
        self.generic_visit(node)
        return GeneratorExp(
            elt=node.elt, generators=ComprehensionSequence(node.generators)
        )

    def visit_Compare(self, node: Compare) -> Compare:
        if isinstance(node.ops, CmpOpSequence):
            return node
        self.generic_visit(node)
        return Compare(
            left=node.left,
            ops=CmpOpSequence(node.ops),
            comparators=ExprSequence(node.comparators),
        )

    def visit_Call(self, node: Call) -> Call:
        if isinstance(node.args, ExprSequence):
            return node
        self.generic_visit(node)
        return Call(
            func=node.func,
            args=ExprSequence(node.args),
            keywords=KeywordSequence(node.keywords),
        )

    def visit_JoinedStr(self, node: JoinedStr) -> JoinedStr:
        if isinstance(node.values, ExprSequence):
            return node
        self.generic_visit(node)
        return JoinedStr(values=ExprSequence(node.values))

    def visit_List(self, node: ListAST) -> ListAST:
        if isinstance(node.elts, ExprSequence):
            return node
        self.generic_visit(node)
        return ListAST(elts=ExprSequence(node.elts), ctx=node.ctx)

    def visit_Tuple(self, node: TupleAST) -> TupleAST:
        if isinstance(node.elts, ExprSequence):
            return node
        self.generic_visit(node)
        return TupleAST(elts=ExprSequence(node.elts), ctx=node.ctx)

    def visit_ExtSlice(self, node: ExtSlice) -> ExtSlice:
        if isinstance(node.dims, SliceSequence):
            return node
        self.generic_visit(node)
        return ExtSlice(dims=SliceSequence(node.dims))

    def visit_arguments(self, node: arguments) -> arguments:
        if isinstance(node.args, ArgSequence):
            return node
        self.generic_visit(node)
        return arguments(
            args=ArgSequence(node.args),
            vararg=node.vararg,
            kwonlyargs=ArgSequence(node.kwonlyargs),
            kw_defaults=ExprSequence(node.kw_defaults),
            kwarg=node.kwarg,
            defaults=ExprSequence(node.defaults),
        )
