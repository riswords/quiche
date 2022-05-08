from ast import (
    NodeTransformer,
    Interactive,
    ClassDef,
    Delete,
    While,
    If,
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
    FormattedValue,
    JoinedStr,
    Attribute,
    Name,
    List as ListAST,
    Tuple as TupleAST,
    comprehension,
    ExceptHandler,
    keyword,
    alias
)

from quiche.pal.pal_block import (
    PALIdentifier,
    PALLeaf,
    IdentifierBlock,
    PALPrimitive,
    StmtBlock,
    ExprBlock,
    CmpopBlock,
    ComprehensionBlock,
    ExceptHandlerBlock,
    KeywordBlock,
    AliasBlock,
)


class PALLifter(NodeTransformer):

    def visit_Interactive(self, node: Interactive) -> Interactive:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return Interactive(body=StmtBlock(node.body))

    def visit_ClassDef(self, node: ClassDef) -> ClassDef:
        if isinstance(node.bases, ExprBlock):
            return node
        self.generic_visit(node)
        return ClassDef(
            name=PALIdentifier(node.name),
            bases=ExprBlock(node.bases),
            keywords=KeywordBlock(node.keywords),
            body=StmtBlock(node.body),
            decorator_list=ExprBlock(node.decorator_list),
        )

    def visit_Delete(self, node: Delete) -> Delete:
        if isinstance(node.targets, ExprBlock):
            return node
        self.generic_visit(node)
        return Delete(targets=ExprBlock(node.targets))

    def visit_While(self, node: While) -> While:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return While(
            test=node.test,
            body=StmtBlock(node.body),
            orelse=StmtBlock(node.orelse),
        )

    def visit_If(self, node: If) -> If:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return If(
            test=node.test,
            body=StmtBlock(node.body),
            orelse=StmtBlock(node.orelse),
        )

    def visit_Try(self, node: Try) -> Try:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return Try(
            body=StmtBlock(node.body),
            handlers=ExceptHandlerBlock(node.handlers),
            orelse=StmtBlock(node.orelse),
            finalbody=StmtBlock(node.finalbody),
        )

    def visit_Import(self, node: Import) -> Import:
        if isinstance(node.names, AliasBlock):
            return node
        self.generic_visit(node)
        return Import(names=AliasBlock(node.names))

    def visit_ImportFrom(self, node: ImportFrom) -> ImportFrom:
        if isinstance(node.names, AliasBlock):
            return node
        self.generic_visit(node)
        return ImportFrom(
            module=PALIdentifier(node.module) if node.module else None,
            names=AliasBlock(node.names),
            level=PALPrimitive[int](node.level) if node.level else None
        )

    def visit_Global(self, node: Global) -> Global:
        if isinstance(node.names, IdentifierBlock):
            return node
        self.generic_visit(node)
        return Global(names=IdentifierBlock([PALIdentifier(name) for name in node.names]))

    def visit_Nonlocal(self, node: Nonlocal) -> Nonlocal:
        if isinstance(node.names, IdentifierBlock):
            return node
        self.generic_visit(node)
        return Nonlocal(names=IdentifierBlock([PALIdentifier(name) for name in node.names]))

    # EXPRESSIONS
    def visit_BoolOp(self, node: BoolOp) -> BoolOp:
        if isinstance(node.values, ExprBlock):
            return node
        self.generic_visit(node)
        return BoolOp(op=node.op, values=ExprBlock(node.values))

    def visit_Dict(self, node: DictAST) -> DictAST:
        if isinstance(node.keys, ExprBlock):
            return node
        self.generic_visit(node)
        return DictAST(keys=ExprBlock(node.keys), values=ExprBlock(node.values))

    def visit_Set(self, node: SetAST) -> SetAST:
        if isinstance(node.elts, ExprBlock):
            return node
        self.generic_visit(node)
        return SetAST(elts=ExprBlock(node.elts))

    def visit_ListComp(self, node: ListComp) -> ListComp:
        if isinstance(node.generators, ComprehensionBlock):
            return node
        self.generic_visit(node)
        return ListComp(elt=node.elt, generators=ComprehensionBlock(node.generators))

    def visit_SetComp(self, node: SetComp) -> SetComp:
        if isinstance(node.generators, ComprehensionBlock):
            return node
        self.generic_visit(node)
        return SetComp(elt=node.elt, generators=ComprehensionBlock(node.generators))

    def visit_DictComp(self, node: DictComp) -> DictComp:
        if isinstance(node.generators, ComprehensionBlock):
            return node
        self.generic_visit(node)
        return DictComp(
            key=node.key,
            value=node.value,
            generators=ComprehensionBlock(node.generators),
        )

    def visit_GeneratorExp(self, node: GeneratorExp) -> GeneratorExp:
        if isinstance(node.generators, ComprehensionBlock):
            return node
        self.generic_visit(node)
        return GeneratorExp(
            elt=node.elt, generators=ComprehensionBlock(node.generators)
        )

    def visit_Compare(self, node: Compare) -> Compare:
        if isinstance(node.ops, CmpopBlock):
            return node
        self.generic_visit(node)
        return Compare(
            left=node.left,
            ops=CmpopBlock(node.ops),
            comparators=ExprBlock(node.comparators),
        )

    def visit_Call(self, node: Call) -> Call:
        if isinstance(node.args, ExprBlock):
            return node
        self.generic_visit(node)
        return Call(
            func=node.func,
            args=ExprBlock(node.args),
            keywords=KeywordBlock(node.keywords),
        )

    def visit_FormattedValue(self, node: FormattedValue) -> FormattedValue:
        if isinstance(node.conversion, PALPrimitive):
            return node
        self.generic_visit(node)
        return FormattedValue(
            value=node.value,
            conversion=PALPrimitive[int](node.conversion) if node.conversion else None,
            format_spec=node.format_spec
        )

    def visit_JoinedStr(self, node: JoinedStr) -> JoinedStr:
        if isinstance(node.values, ExprBlock):
            return node
        self.generic_visit(node)
        return JoinedStr(values=ExprBlock(node.values))

    def visit_Attribute(self, node: Attribute) -> Attribute:
        if isinstance(node.attr, PALIdentifier):
            return node
        self.generic_visit(node)
        return Attribute(value=node.value, attr=PALIdentifier(node.attr), ctx=node.ctx)

    def visit_Name(self, node: Name) -> PALLeaf:
        return PALLeaf("name", Name, node.id, node.ctx)

    def visit_List(self, node: ListAST) -> ListAST:
        if isinstance(node.elts, ExprBlock):
            return node
        self.generic_visit(node)
        return ListAST(elts=ExprBlock(node.elts), ctx=node.ctx)

    def visit_Tuple(self, node: TupleAST) -> TupleAST:
        if isinstance(node.elts, ExprBlock):
            return node
        self.generic_visit(node)
        return TupleAST(elts=ExprBlock(node.elts), ctx=node.ctx)

    def visit_comprehension(self, node: comprehension) -> comprehension:
        if isinstance(node.ifs, ExprBlock):
            return node
        self.generic_visit(node)
        return comprehension(
            target=node.target,
            iter=node.iter,
            ifs=ExprBlock(node.ifs),
            is_async=PALPrimitive[int](node.is_async),
        )

    def visit_ExceptHandler(self, node: ExceptHandler) -> ExceptHandler:
        if isinstance(node.body, StmtBlock):
            return node
        self.generic_visit(node)
        return ExceptHandler(
            type=node.type,
            name=PALIdentifier(node.name) if node.name else None,
            body=StmtBlock(node.body),
        )

    def visit_keyword(self, node: keyword) -> keyword:
        if isinstance(node.arg, PALIdentifier):
            return node
        self.generic_visit(node)
        return keyword(arg=PALIdentifier(node.arg) if node.arg else None, value=node.value)

    def visit_alias(self, node: alias) -> alias:
        if isinstance(node.name, PALIdentifier):
            return node
        self.generic_visit(node)
        return alias(name=PALIdentifier(node.name), asname=PALIdentifier(node.asname) if node.asname else None)
