from ast import (
    Module,
    Suite,
    FunctionDef,
    AsyncFunctionDef,
    Assign,
    AnnAssign,
    For,
    AsyncFor,
    With,
    AsyncWith,
    Num,
    Str,
    Bytes,
    NameConstant,
    ExtSlice,
    arguments,
    arg,
)

from quiche.pal.pal_block import (
    PALIdentifier,
    PALLeaf,
    PALPrimitive,
    StmtBlock,
    ExprBlock,
    SliceBlock,
    ArgBlock,
    WithItemBlock,
)

from quiche.pal.pal_lifter import PALLifter


class PALLift37(PALLifter):
    def visit_Module(self, node: Module) -> Module:
        # Short-circuit: assume if the body is a StmtBlock, it's already
        # been transformed. NOTE: may need to revisit this later if this
        # transform is applied to fix-up after other modifications.
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return Module(body=StmtBlock(node.body))

    def visit_Suite(self, node: Suite) -> Suite:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return Suite(body=StmtBlock(node.body))

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return FunctionDef(
            name=PALIdentifier(node.name),
            args=node.args,
            body=StmtBlock(node.body),
            decorator_list=ExprBlock(node.decorator_list),
            returns=node.returns,
        )

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> AsyncFunctionDef:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return AsyncFunctionDef(
            name=PALIdentifier(node.name),
            args=node.args,
            body=StmtBlock(node.body),
            decorator_list=ExprBlock(node.decorator_list),
            returns=node.returns,
        )

    def visit_Assign(self, node: Assign) -> Assign:
        if isinstance(node.targets, ExprBlock):
            return node
        self.generic_visit(node)
        return Assign(targets=ExprBlock(node.targets), value=node.value)

    def visit_AnnAssign(self, node: AnnAssign) -> AnnAssign:
        if isinstance(node.simple, PALPrimitive):
            return node
        self.generic_visit(node)
        return AnnAssign(target=node.target, value=node.value, simple=PALPrimitive[int](node.simple))

    def visit_For(self, node: For) -> For:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return For(
            target=node.target,
            iter=node.iter,
            body=StmtBlock(node.body),
            orelse=StmtBlock(node.orelse),
        )

    def visit_AsyncFor(self, node: AsyncFor) -> AsyncFor:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return AsyncFor(
            target=node.target,
            iter=node.iter,
            body=StmtBlock(node.body),
            orelse=StmtBlock(node.orelse),
        )

    def visit_With(self, node: With) -> With:
        if isinstance(node.items, WithItemBlock):
            return node
        self.generic_visit(node)
        return With(items=WithItemBlock(node.items), body=StmtBlock(node.body))

    def visit_AsyncWith(self, node: AsyncWith) -> AsyncWith:
        if isinstance(node.items, WithItemBlock):
            return node
        self.generic_visit(node)
        return AsyncWith(
            items=WithItemBlock(node.items), body=StmtBlock(node.body)
        )

    # EXPRESSIONS
    def visit_Num(self, node: Num) -> PALLeaf[complex]:
        return PALLeaf[complex](type(node.n).__name__, Num, node.n)

    def visit_Str(self, node: Str) -> PALLeaf[str]:
        return PALLeaf[str]("str", Str, node.s)

    def visit_Bytes(self, node: Bytes) -> PALLeaf[bytes]:
        return PALLeaf[bytes]("bytes", Bytes, node.s)

    def visit_NameConstant(self, node: NameConstant) -> PALLeaf:
        return PALLeaf[bool]("bool", NameConstant, node.value)

    def visit_ExtSlice(self, node: ExtSlice) -> ExtSlice:
        if isinstance(node.dims, SliceBlock):
            return node
        self.generic_visit(node)
        return ExtSlice(dims=SliceBlock(node.dims))

    def visit_arguments(self, node: arguments) -> arguments:
        if isinstance(node.args, ArgBlock):
            return node
        self.generic_visit(node)
        return arguments(
            args=ArgBlock(node.args),
            vararg=node.vararg,
            kwonlyargs=ArgBlock(node.kwonlyargs),
            kw_defaults=ExprBlock(node.kw_defaults),
            kwarg=node.kwarg,
            defaults=ExprBlock(node.defaults),
        )

    def visit_arg(self, node: arg) -> arg:
        if isinstance(node.arg, PALIdentifier):
            return node
        self.generic_visit(node)
        return arg(arg=PALIdentifier(node.arg), annotation=node.annotation)
