import ast
import os
from sys import version_info

from quiche.pyast.ast_quiche_tree import ASTQuicheTree
from quiche.egraph import EGraph
import quiche.pyast.pal.pal_block as ASTQT
from quiche.pyast.ast_size_cost_model import ASTSizeCostModel
from quiche.pyast.ast_heuristic_cost_model import ASTHeuristicCostModel
from quiche.pyast.ast_constant_folding import ASTConstantFolding
from quiche.analysis import MinimumCostExtractor


def input_directory():
    return os.path.join(os.path.dirname(__file__), "input")


def setup_sqrt_tree():
    fname = os.path.join(input_directory(), "test_sqrt.py")
    tree_root = ASTQuicheTree(fname)
    return tree_root


def setup_constant_folding_tree():
    fname = os.path.join(input_directory(), "constant_folding.py")
    tree_root = ASTQuicheTree(fname)
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
    if version_info[:2] <= (3, 7):
        assert rule.lhs.children()[0].value() == ("bool", ast.NameConstant, True)
    elif version_info[:2] >= (3, 8):
        assert rule.lhs.children()[0].value() == ("bool", ast.Constant, True, None)

    # Verify LHS (StmtBlock (Expr (Name __quiche__body))) structure
    stmt_sequence = rule.lhs.children()[1]
    assert stmt_sequence.value().__name__ == "StmtBlock"
    assert len(stmt_sequence.children()) == 1
    assert stmt_sequence.children()[0].value().__name__ == "Expr"
    # assert stmt_sequence.children()[0].children()[0].value().__name__ == "Name"
    assert stmt_sequence.children()[0].children()[0].value()[:3] == ("name", ast.Name, "__quiche__body")
    assert type(stmt_sequence.children()[0].children()[0].value()[3]) == ast.Load
    assert stmt_sequence.children()[0].children()[0].root.kind == "name"
    assert stmt_sequence.children()[0].children()[0].root.constr == ast.Name
    assert stmt_sequence.children()[0].children()[0].root.args[0] == "__quiche__body"
    assert type(stmt_sequence.children()[0].children()[0].root.args[1]) == ast.Load

    # Verify RHS type
    assert isinstance(rule.rhs, ASTQuicheTree)
    assert rule.rhs.value().__name__ == "While"
    assert len(rule.rhs.children()) == 3

    # Verify RHS "1" structure: (Num int, value = 1)
    assert rule.rhs.children()[0].children() == []
    if version_info[:2] <= (3, 7):
        assert rule.rhs.children()[0].value() == ("int", ast.Num, 1)
    elif version_info >= (3, 8):
        assert rule.rhs.children()[0].value() == ("int", ast.Constant, 1, None)

    # Verify RHS (StmtBlock (Expr (Name __quiche__body))) structure
    stmt_sequence = rule.rhs.children()[1]
    assert stmt_sequence.value().__name__ == "StmtBlock"
    assert len(stmt_sequence.children()) == 1
    assert stmt_sequence.children()[0].value().__name__ == "Expr"
    assert stmt_sequence.children()[0].children()[0].value()[:3] == ("name", ast.Name, "__quiche__body")
    assert type(stmt_sequence.children()[0].children()[0].value()[3]) == ast.Load


def test_make_rule2():
    rule = make_rule_2()
    # Verify LHS type
    assert isinstance(rule.lhs, ASTQuicheTree)
    assert rule.lhs.value() == ast.While
    assert len(rule.lhs.children()) == 3

    # Verify LHS "True" structure: (NameConstant bool, value = True)
    assert rule.lhs.children()[0].value()[0] == "bool"
    if version_info[:2] <= (3, 7):
        assert rule.lhs.children()[0].value()[1] == ast.NameConstant
    elif version_info[:2] >= (3, 8):
        assert rule.lhs.children()[0].value()[1] == ast.Constant
    assert rule.lhs.children()[0].value()[2] is True
    assert rule.lhs.children()[1].children()[0].root.value

    # Verify LHS (StmtBlock (Expr (Str __quiche__body))) structure
    stmt_sequence = rule.lhs.children()[1]
    assert stmt_sequence.value() == ASTQT.StmtBlock
    assert len(stmt_sequence.children()) == 1
    assert stmt_sequence.children()[0].value() == ast.Expr
    if version_info[:2] <= (3, 7):
        assert stmt_sequence.children()[0].children()[0].value() == ("str", ast.Str, "__quiche__body")
        assert stmt_sequence.children()[0].children()[0].root.constr == ast.Str
        assert stmt_sequence.children()[0].children()[0].root.args == ("__quiche__body",)
    elif version_info[:2] >= (3, 8):
        assert stmt_sequence.children()[0].children()[0].value() == ("str", ast.Constant, "__quiche__body", None)
        assert stmt_sequence.children()[0].children()[0].root.kind == "str"
        assert stmt_sequence.children()[0].children()[0].root.constr == ast.Constant
        assert stmt_sequence.children()[0].children()[0].root.args == ("__quiche__body", None)

    # Verify RHS type
    assert isinstance(rule.rhs, ASTQuicheTree)
    assert rule.rhs.value() == ast.While
    assert len(rule.rhs.children()) == 3

    # Verify RHS "1" structure: (Num int, value = 1)
    if version_info[:2] <= (3, 7):
        assert rule.rhs.children()[0].value() == ("int", ast.Num, 1)
        assert rule.rhs.children()[0].root.kind == "int"
        assert rule.rhs.children()[0].root.constr == ast.Num
        assert rule.rhs.children()[0].root.args == (1,)
    elif version_info[:2] >= (3, 8):
        assert rule.rhs.children()[0].value() == ("int", ast.Constant, 1, None)
        assert rule.rhs.children()[0].root.kind == "int"
        assert rule.rhs.children()[0].root.constr == ast.Constant
        assert rule.rhs.children()[0].root.args == (1, None)

    # Verify RHS (StmtBlock (Expr (Str __quiche__body))) structure
    stmt_sequence = rule.rhs.children()[1]
    assert stmt_sequence.value() == ASTQT.StmtBlock
    assert len(stmt_sequence.children()) == 1
    assert stmt_sequence.children()[0].value() == ast.Expr
    if version_info[:2] <= (3, 7):
        assert stmt_sequence.children()[0].children()[0].value() == ("str", ast.Str, "__quiche__body")
        assert stmt_sequence.children()[0].children()[0].root.kind == "str"
        assert stmt_sequence.children()[0].children()[0].root.constr == ast.Str
        assert stmt_sequence.children()[0].children()[0].root.args == ("__quiche__body",)
    elif version_info[:2] >= (3, 8):
        assert stmt_sequence.children()[0].children()[0].value() == ("str", ast.Constant, "__quiche__body", None)
        assert stmt_sequence.children()[0].children()[0].root.kind == "str"
        assert stmt_sequence.children()[0].children()[0].root.constr == ast.Constant
        assert stmt_sequence.children()[0].children()[0].root.args == ("__quiche__body", None)


def test_ematch_rule1():
    quiche_tree = setup_sqrt_tree()
    actual = EGraph(quiche_tree)
    rule = make_rule_1()

    match = actual.ematch(rule.lhs, actual.eclasses())
    key = list(actual.eclasses().keys())[52]

    assert match
    assert len(match) == 1
    print("MATCHED: ", match)
    assert key in match[0]


def test_ematch_rule2():
    quiche_tree = setup_sqrt_tree()
    actual = EGraph(quiche_tree)
    rule = make_rule_2()

    match = actual.ematch(rule.lhs, actual.eclasses())
    key = list(actual.eclasses().keys())[52]

    assert match
    assert len(match) == 1
    assert key in match[0]


def test_apply_rule1():
    quiche_tree = setup_sqrt_tree()
    actual = EGraph(quiche_tree)
    rule = make_rule_1()

    assert not actual.is_saturated()
    actual.apply_rules([rule])
    if version_info[:2] <= (3, 7):
        assert actual.version == 145
    else:
        assert actual.version == 146


def test_extract_identity():
    quiche_tree = setup_sqrt_tree()
    fname = os.path.join(input_directory(), "test_sqrt.py")
    with open(fname, "r") as f:
        expected = f.read()
    eg = EGraph(quiche_tree)
    root = eg.root
    cost_model = ASTSizeCostModel()
    extractor = MinimumCostExtractor()
    # print("ECLASSES: ", actual.eclasses())
    extracted = extractor.extract(cost_model, eg, root, ASTQuicheTree.make_node)
    actual = extracted.to_source_string()
    assert expected == actual


def test_extract_rule1():
    quiche_tree = setup_sqrt_tree()
    fname = os.path.join(input_directory(), "test_sqrt.py")
    with open(fname, "r") as f:
        expected_lines = f.read().splitlines()
    eg = EGraph(quiche_tree)
    rule = make_rule_1()
    assert not eg.is_saturated()
    eg.apply_rules([rule])
    if version_info[:2] <= (3, 7):
        assert eg.version == 145
    else:
        assert eg.version == 146

    root = eg.root
    cost_model = ASTHeuristicCostModel()
    extractor = MinimumCostExtractor()
    extracted = extractor.extract(cost_model, eg, root, ASTQuicheTree.make_node)
    actual_lines = extracted.to_source_string().splitlines()

    for idx, (act, exp) in enumerate(zip(actual_lines, expected_lines)):
        if idx != 10:
            assert act == exp
        else:
            assert act == "    while 1:"
            assert exp == "    while True:"


# Constant Folding
def test_constant_folding():
    tree = setup_constant_folding_tree()
    fname = os.path.join(input_directory(), "constant_folding.py")
    with open(fname, "r") as f:
        original_lines = f.read().splitlines()
    analysis = ASTConstantFolding()
    eg = EGraph(tree, analysis)

    cost_model = ASTSizeCostModel()
    extractor = MinimumCostExtractor()
    extracted = extractor.extract(cost_model, eg, eg.root, ASTQuicheTree.make_node)
    actual_lines = extracted.to_source_string().splitlines()

    for idx, (res, pre) in enumerate(zip(actual_lines, original_lines)):
        if idx == 9:
            assert pre == "    return 1 + 2"
            assert res == "    return 3"
        elif idx == 17:
            assert pre == "    return (1 + 2) + 3"
            assert res == "    return 6"
        elif idx == 21:
            assert pre == "    return 1 + (2 + 3)"
            assert res == "    return 6"
        elif idx == 25:
            assert pre == "    return 1 + 2 + 3 + 2"
            assert res == "    return 8"
        elif idx == 33:
            assert pre == "    return 1 + 2 + x"
            assert res == "    return 3 + x"
        elif idx == 49:
            assert pre == "    y = 5 - 2"
            assert res == "    y = 3"
        elif idx == 54:
            assert pre == "    y = (5 - 4) - 3"
            assert res == "    y = -2"
        elif idx == 59:
            assert pre == "    y = 5 - (4 - 3)"
            assert res == "    y = 4"
        elif idx == 69:
            assert pre == "    y = x - (3 - 2)"
            assert res == "    y = x - 1"
        else:
            assert res == pre, "Line {}: {} != {}".format(idx, res, pre)
