import ast

from quiche.ast_quiche_tree import ASTQuicheTree
from quiche.egraph import EGraph
import quiche.insert_ast_block_traversal as ASTQT
from quiche.ast_size_cost_model import ASTSizeCostModel
from quiche.analysis import MinimumCostExtractor

from quiche.ast_heuristic_cost_model import ASTHeuristicCostModel


def setup_tree():
    tree_root = ASTQuicheTree("tests/test_sqrt.py")
    return tree_root


def make_rule_1():
    # test rule where body is a variable
    return ASTQuicheTree.make_rule(
        "while True:\n\t__quiche__body", "while 1:\n\t__quiche__body"
    )


def make_rule_2():
    # test rule where body is a string
    return ASTQuicheTree.make_rule(
        "while True:\n\t'__quiche__body'", "while 1:\n\t'__quiche__body'"
    )


def test_make_rule1():
    rule = make_rule_1()
    # Verify LHS type
    assert isinstance(rule.lhs, ASTQuicheTree)
    assert rule.lhs.value().__name__ == "While"
    assert len(rule.lhs.children()) == 3

    # Verify LHS "True" structure: (NameConstant bool, value = True)
    assert rule.lhs.children()[0].value() == (ast.NameConstant, True)

    # Verify LHS (StmtSequence (Expr (Name __quiche__body))) structure
    stmt_sequence = rule.lhs.children()[1]
    assert stmt_sequence.value().__name__ == "StmtSequence"
    assert len(stmt_sequence.children()) == 1
    assert stmt_sequence.children()[0].value().__name__ == "Expr"
    # assert stmt_sequence.children()[0].children()[0].value().__name__ == "Name"
    assert stmt_sequence.children()[0].children()[0].value()[0] == ast.Name
    assert stmt_sequence.children()[0].children()[0].value()[1] == "__quiche__body"
    assert type(stmt_sequence.children()[0].children()[0].value()[2]) == ast.Load
    assert stmt_sequence.children()[0].children()[0].root.id == "__quiche__body"

    # Verify RHS type
    assert isinstance(rule.rhs, ASTQuicheTree)
    assert rule.rhs.value().__name__ == "While"
    assert len(rule.rhs.children()) == 3

    # Verify RHS "1" structure: (Num int, value = 1)
    assert rule.rhs.children()[0].value() == (ast.Num, 1)
    assert rule.rhs.children()[0].children() == []

    # Verify RHS (StmtSequence (Expr (Name __quiche__body))) structure
    stmt_sequence = rule.rhs.children()[1]
    assert stmt_sequence.value().__name__ == "StmtSequence"
    assert len(stmt_sequence.children()) == 1
    assert stmt_sequence.children()[0].value().__name__ == "Expr"
    assert stmt_sequence.children()[0].children()[0].value()[0] == ast.Name
    assert stmt_sequence.children()[0].children()[0].value()[1] == "__quiche__body"
    # assert stmt_sequence.children()[0].children()[0].root.id == "__quiche__body"


def test_make_rule2():
    rule = make_rule_2()
    # Verify LHS type
    assert isinstance(rule.lhs, ASTQuicheTree)
    assert rule.lhs.value() == ast.While
    assert len(rule.lhs.children()) == 3

    # Verify LHS "True" structure: (NameConstant bool, value = True)
    assert rule.lhs.children()[0].value()[0] == ast.NameConstant
    assert rule.lhs.children()[0].value()[1] is True
    assert rule.lhs.children()[1].children()[0].root.value

    # Verify LHS (StmtSequence (Expr (Str __quiche__body))) structure
    stmt_sequence = rule.lhs.children()[1]
    assert stmt_sequence.value() == ASTQT.StmtSequence
    assert len(stmt_sequence.children()) == 1
    assert stmt_sequence.children()[0].value() == ast.Expr
    assert stmt_sequence.children()[0].children()[0].value()[0] == ast.Str
    assert stmt_sequence.children()[0].children()[0].value()[1] == "__quiche__body"
    assert stmt_sequence.children()[0].children()[0].root.s == "__quiche__body"

    # Verify RHS type
    assert isinstance(rule.rhs, ASTQuicheTree)
    assert rule.rhs.value() == ast.While
    assert len(rule.rhs.children()) == 3

    # Verify RHS "1" structure: (Num int, value = 1)
    assert rule.rhs.children()[0].value()[0] == ast.Num
    assert rule.rhs.children()[0].value()[1] == 1
    assert rule.rhs.children()[0].root.n == 1

    # Verify RHS (StmtSequence (Expr (Str __quiche__body))) structure
    stmt_sequence = rule.rhs.children()[1]
    assert stmt_sequence.value() == ASTQT.StmtSequence
    assert len(stmt_sequence.children()) == 1
    assert stmt_sequence.children()[0].value() == ast.Expr
    assert stmt_sequence.children()[0].children()[0].value()[0] == ast.Str
    assert stmt_sequence.children()[0].children()[0].value()[1] == "__quiche__body"
    assert stmt_sequence.children()[0].children()[0].root.s == "__quiche__body"


def test_ematch_rule1():
    quiche_tree = setup_tree()
    actual = EGraph(quiche_tree)
    rule = make_rule_1()

    match = actual.ematch(rule.lhs, actual.eclasses())
    key = list(actual.eclasses().keys())[48]

    assert match
    assert len(match) == 1
    # print("MATCHED: ", match)
    assert key in match[0]


def test_ematch_rule2():
    quiche_tree = setup_tree()
    actual = EGraph(quiche_tree)
    rule = make_rule_2()

    match = actual.ematch(rule.lhs, actual.eclasses())
    key = list(actual.eclasses().keys())[48]

    assert match
    assert len(match) == 1
    assert key in match[0]


def test_apply_rule1():
    quiche_tree = setup_tree()
    actual = EGraph(quiche_tree)
    rule = make_rule_1()

    actual.apply_rules([rule])
    assert actual.version == 134


def test_extract_identity():
    quiche_tree = setup_tree()
    with open("tests/test_sqrt.py", "r") as f:
        expected = f.read()
    eg = EGraph(quiche_tree)
    root = eg.root
    cost_model = ASTSizeCostModel()
    extractor = MinimumCostExtractor()
    # print("ECLASSES: ", actual.eclasses())
    extracted = extractor.extract(cost_model, eg, root)
    actual = extracted.to_source_string()
    assert expected == actual


def test_extract_rule1():
    quiche_tree = setup_tree()
    with open("tests/test_sqrt.py", "r") as f:
        expected_lines = f.read().splitlines()
    eg = EGraph(quiche_tree)
    rule = make_rule_1()
    eg.apply_rules([rule])
    assert eg.version == 134

    root = eg.root
    cost_model = ASTHeuristicCostModel()
    extractor = MinimumCostExtractor()
    extracted = extractor.extract(cost_model, eg, root)
    actual_lines = extracted.to_source_string().splitlines()

    for idx, (act, exp) in enumerate(zip(actual_lines, expected_lines)):
        if idx != 10:
            assert act == exp
        else:
            assert act == "    while 1:"
            assert exp == "    while True:"
