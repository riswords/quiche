from ast import (
    MatchMapping,
    MatchSequence,
    MatchSingleton,
    Module,
    FunctionType,
    FunctionDef,
    AsyncFunctionDef,
    Assign,
    AnnAssign,
    For,
    AsyncFor,
    With,
    AsyncWith,
    Match,
    Constant,
    Attribute,
    arguments,
    arg,
    match_case,
    MatchClass,
    MatchStar,
    MatchAs,
    MatchOr,
)

from quiche.pyast.pal.pal_block import (
    IdentifierBlock,
    PALIdentifier,
    PALLeaf,
    PALPrimitive,
    StmtBlock,
    ExprBlock,
    ArgBlock,
    WithItemBlock,
    TypeIgnoreBlock,
    MatchCaseBlock,
    PatternBlock,
)

from quiche.pyast.pal.pal_lifter import PALLifter


class PALLift310(PALLifter):
    def visit_Module(self, node: Module) -> Module:
        # Short-circuit: assume if the body is a StmtBlock, it's already
        # been transformed. NOTE: may need to revisit this later if this
        # transform is applied to fix-up after other modifications.
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return Module(body=StmtBlock(node.body), type_ignores=TypeIgnoreBlock(node.type_ignores))

    # visit_Interactive provided by PALLifter
    # visit_Expression not needed

    def visit_FunctionType(self, node: FunctionType) -> FunctionType:
        if isinstance(node.argtypes, ExprBlock):
            return node
        self.generic_visit(node)
        return FunctionType(argtypes=ExprBlock(node.argtypes), returns=node.returns)

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
            type_comment=PALPrimitive[str](node.type_comment) if node.type_comment else None,
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
            type_comment=PALPrimitive[str](node.type_comment) if node.type_comment else None,
        )

    # visit_ClassDef provided by PALLifter
    # visit_Return not needed
    # visit_Delete provided by PALLifter

    def visit_Assign(self, node: Assign) -> Assign:
        if isinstance(node.targets, ExprBlock):
            return node
        self.generic_visit(node)
        return Assign(
            targets=ExprBlock(node.targets),
            value=node.value,
            type_comment=PALPrimitive[str](node.type_comment) if node.type_comment else None,
        )

    # visit_AugAssign not needed

    def visit_AnnAssign(self, node: AnnAssign) -> AnnAssign:
        if isinstance(node.simple, PALPrimitive):
            return node
        self.generic_visit(node)
        return AnnAssign(
            target=node.target,
            annotation=node.annotation,
            value=node.value,
            simple=PALPrimitive[int](node.simple)
        )

    def visit_For(self, node: For) -> For:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return For(
            target=node.target,
            iter=node.iter,
            body=StmtBlock(node.body),
            orelse=StmtBlock(node.orelse),
            type_comment=PALPrimitive[str](node.type_comment) if node.type_comment else None,
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
            type_coment=PALPrimitive[str](node.type_comment) if node.type_comment else None,
        )

    # visit_While provided by PALLifter
    # visit_If provided by PALLifter

    def visit_With(self, node: With) -> With:
        if isinstance(node.items, WithItemBlock):
            return node
        self.generic_visit(node)
        return With(
            items=WithItemBlock(node.items),
            body=StmtBlock(node.body),
            type_comment=PALPrimitive[str](node.type_comment) if node.type_comment else None,
        )

    def visit_AsyncWith(self, node: AsyncWith) -> AsyncWith:
        if isinstance(node.items, WithItemBlock):
            return node
        self.generic_visit(node)
        return AsyncWith(
            items=WithItemBlock(node.items),
            body=StmtBlock(node.body),
            type_comment=PALPrimitive[str](node.type_comment) if node.type_comment else None,
        )

    def visit_Match(self, node: Match) -> Match:
        if isinstance(node.cases, MatchCaseBlock):
            return node
        self.generic_visit(node)
        return Match(
            subject=node.subject,
            cases=MatchCaseBlock(node.cases),
        )

    # visit_Raise not needed
    # visit_Try provided by PALLifter
    # visit_Assert not needed
    # visit_Import provided by PALLifter
    # visit_ImportFrom provided by PALLifter
    # visit_Global provided by PALLifter
    # visit_Nonlocal provided by PALLifter
    # visit_Expr not needed
    # visit_Pass/Break/Continue not needed

    # EXPRESSIONS

    # visit_BoolOp provided by PALLifter
    # visit_NamedExpr, BinOp, UnaryOp, Lambda, IfExp
    # visit_Dict, Set, ListComp, SetComp, DictComp, GeneratorExp provided by
    #   PALLifter
    # visit_Await, Yield, YieldFrom not needed
    # visit_Compare, Call, FormattedValue, JoinedStr provided by PALLifter

    def visit_Constant(self, node: Constant) -> PALLeaf:
        kind = type(node.value).__name__
        return PALLeaf(kind, Constant, node.value, getattr(node, "kind", None))

    def visit_Attribute(self, node: Attribute) -> Attribute:
        if isinstance(node.attr, PALIdentifier):
            return node
        self.generic_visit(node)
        return Attribute(
            value=node.value,
            attr=PALIdentifier(node.attr),
            ctx=PALLeaf("context", node.ctx.__class__),
        )

    # visit_Subscript, Starred not needed
    # visit_Name, List, Tuple provided by PALLifter
    # visit_Slice not needed
    # visit_comprehension, ExceptHandler provided by PALLifter

    def visit_arguments(self, node: arguments) -> arguments:
        if isinstance(node.args, ArgBlock):
            return node
        self.generic_visit(node)
        return arguments(
            posonlyargs=ArgBlock(node.posonlyargs),
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
        return arg(
            arg=PALIdentifier(node.arg),
            annotation=node.annotation,
            type_comment=PALPrimitive[str](node.type_comment) if node.type_comment else None,
        )

    # visit_keyword, alias provided by PALLifter
    # visit_withitem not needed

    def visit_match_case(self, node: match_case) -> match_case:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return match_case(
            pattern=node.pattern,
            guard=node.guard,
            body=StmtBlock(node.body),
        )

    # vsiit_MatchValue not needed

    def visit_MatchSingleton(self, node: MatchSingleton) -> MatchSingleton:
        if isinstance(node.value, PALLeaf):
            return node
        return MatchSingleton(value=PALPrimitive(node.value))

    def visit_MatchSequence(self, node: MatchSequence) -> MatchSequence:
        if isinstance(node.patterns, PatternBlock):
            return node
        self.generic_visit(node)
        return MatchSequence(patterns=PatternBlock(node.patterns))

    def visit_MatchMapping(self, node: MatchMapping) -> MatchMapping:
        if isinstance(node.keys, ExprBlock):
            return node
        self.generic_visit(node)
        return MatchMapping(
            keys=ExprBlock(node.keys),
            patterns=PatternBlock(node.patterns),
            rest=PALIdentifier(node.rest) if node.rest else None,
        )

    def visit_MatchClass(self, node: MatchClass) -> MatchClass:
        if isinstance(node.patterns, PatternBlock):
            return node
        self.generic_visit(node)
        return MatchClass(
            cls=node.cls,
            patterns=PatternBlock(node.patterns),
            kwd_attrs=IdentifierBlock([PALIdentifier(ident) for ident in node.kwd_attrs]),
            kwd_patterns=PatternBlock(node.kwd_patterns),
        )

    def visit_MatchStar(self, node: MatchStar) -> MatchStar:
        # NOTE: Might need to add a hasattr check
        if isinstance(node.name, PALIdentifier):
            return node
        return MatchStar(name=PALIdentifier(node.name) if node.name else None)

    def visit_MatchAs(self, node: MatchAs) -> MatchAs:
        if isinstance(node.name, PALIdentifier):
            return node
        self.generic_visit(node)
        return MatchAs(
            pattern=node.pattern,
            name=PALIdentifier(node.name) if node.name else None
        )

    def visit_MatchOr(self, node: MatchOr) -> MatchOr:
        if isinstance(node.patterns, PatternBlock):
            return node
        self.generic_visit(node)
        return MatchOr(patterns=PatternBlock(node.patterns))
