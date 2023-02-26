from quiche import EGraph, MinimumCostExtractor, Rule
from quiche.lang.expr_lang import ExprNode, ExprNodeCost, ExprTree

from .util import verify_egraph_shape  # , print_egraph


def make_rules():
    rules = [
        ExprTree.make_rule(lambda x: (x * 2, x << 1)),  # mult by 2 is shift left 1
        ExprTree.make_rule(
            lambda x, y, z: ((x * y) / z, x * (y / z))
        ),  # reassociate *,/
        ExprTree.make_rule(lambda x: (x / x, ExprNode(1, ()))),  # x/x = 1
        ExprTree.make_rule(lambda x: (x * 1, x)),  # simplify mult by 1
    ]
    return rules


def times_divide():
    # return ExprNode.exp(lambda a: (a * 2) / 2)
    return (ExprNode('a', ()) * 2) / 2


def shift():
    # return ExprNode.exp(lambda a: a << 1)
    return ExprNode('a', ()) << 1


def times2():
    # return ExprNode.exp(lambda a: a * 2)
    return ExprNode('a', ()) * 2


def test_add_times_divide():
    actual = EGraph(ExprTree(times_divide()))
    expected = {
        "e0": {"a": [()]},
        "e1": {"2": [()]},
        "e2": {"*": [("e0", "e1")]},
        "e3": {"/": [("e2", "e1")]},
    }
    assert verify_egraph_shape(actual, expected)


def test_add_shift():
    actual = EGraph(ExprTree(shift()))
    expected = {
        "e0": {"a": [()]},
        "e1": {"1": [()]},
        "e2": {"<<": [("e0", "e1")]},
    }
    assert verify_egraph_shape(actual, expected)


def test_add_two_exprs():
    actual = EGraph(ExprTree(times_divide()))
    _ = actual.add(ExprTree(shift()))
    expected = {
        "e0": {"a": [()]},
        "e1": {"2": [()]},
        "e2": {"*": [("e0", "e1")]},
        "e3": {"/": [("e2", "e1")]},
        "e4": {"1": [()]},
        "e5": {"<<": [("e0", "e4")]},
    }
    assert verify_egraph_shape(actual, expected)


def test_merge_exprs():
    actual = EGraph(ExprTree(times_divide()))
    times_root = actual.add(ExprTree(times2()))
    shift_root = actual.add(ExprTree(shift()))
    actual.merge(times_root, shift_root)
    actual.rebuild()

    expected = {
        "e0": {"a": [()]},
        "e1": {"2": [()]},
        "e2": {"<<": [("e0", "e4")], "*": [("e0", "e1")]},
        "e3": {"/": [("e2", "e1")]},
        "e4": {"1": [()]},
    }
    assert verify_egraph_shape(actual, expected)


def test_expr_ematch():
    actual = EGraph(ExprTree(times_divide()))
    # Rule to reassociate *,/
    rule = ExprTree.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z)))
    matches = actual.ematch(rule.lhs, actual.eclasses())

    # expect exactly one match
    assert len(matches) == 1
    match = matches[0]

    # expect match to be (e3, {x: e0, y: e1, z: e1})
    assert len(match) == 2
    assert str(match[0]) == "e3"

    assert len(match[1]) == 3
    assert str(match[1]["x"]) == "e0"
    assert str(match[1]["y"]) == "e1"
    assert str(match[1]["z"]) == "e1"


def test_expr_subst():
    actual = EGraph(ExprTree(times_divide()))
    shift_root = actual.add(ExprTree(shift()))
    times2_root = actual.add(ExprTree(times2()))
    actual.merge(times2_root, shift_root)
    actual.rebuild()
    # Rule to reassociate *,/
    rule = ExprTree.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z)))
    matches = actual.ematch(rule.lhs, actual.eclasses())
    lhs, env = matches[0]
    rhs = rule._subst(actual, rule.rhs, env)

    assert str(lhs) == "e3"
    assert str(rhs) == "e7"

    expected = {
        "e0": {"a": [()]},
        "e1": {"2": [()]},
        "e2": {"<<": [("e0", "e4")], "*": [("e0", "e1")]},
        "e3": {"/": [("e2", "e1")]},
        "e4": {"1": [()]},
        "e6": {"/": [("e1", "e1")]},
        "e7": {"*": [("e0", "e6")]},
    }
    verify_egraph_shape(actual, expected)


def test_apply_rules():
    actual = EGraph(ExprTree(times_divide()))
    rules = [
        # Multiply x by 2 === shift x left by 1
        ExprTree.make_rule(lambda x: (x * 2, x << 1)),
        # Reassociate *,/
        ExprTree.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z))),
        # x/x = 1
        ExprTree.make_rule(lambda x: (x / x, ExprNode(1, ()))),
        # Simplify x * 1 === x
        ExprTree.make_rule(lambda x: (x * 1, x)),
    ]
    versions = [4, 10, 11, 12]
    for version in versions:
        assert actual.version == version
        Rule.apply_rules(rules, actual)
    assert actual.version == versions[-1]
    expected = {
        "e0": {"a": [()], "/": [("e2", "e1")], "*": [("e0", "e4")]},
        "e1": {"2": [()]},
        "e2": {"*": [("e0", "e1")], "<<": [("e0", "e4")]},
        "e4": {"1": [()], "/": [("e1", "e1")]},
    }
    assert verify_egraph_shape(actual, expected)


def test_extract():
    # Verify rule application
    actual = EGraph(ExprTree(times_divide()))
    root = actual.root
    rules = [
        # Multiply x by 2 === shift x left by 1
        ExprTree.make_rule(lambda x: (x * 2, x << 1)),
        # Reassociate *,/
        ExprTree.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z))),
        # x/x = 1
        ExprTree.make_rule(lambda x: (x / x, ExprNode(1, ()))),
        # Simplify x * 1 === x
        ExprTree.make_rule(lambda x: (x * 1, x)),
    ]
    versions = [4, 10, 11, 12]
    best_terms = ["(/ (* a 2) 2)", "(/ (<< a 1) 2)", "(* a 1)", "a"]
    for version, term in zip(versions, best_terms):
        assert actual.version == version
        # Verify extracted term is correct
        cost_model = ExprNodeCost()
        cost_analysis = MinimumCostExtractor()
        extracted = cost_analysis.extract(
            cost_model, actual, root.find(), ExprTree.make_node
        )
        assert str(extracted) == term
        Rule.apply_rules(rules, actual)
    assert actual.version == versions[-1]
    assert (
        str(cost_analysis.extract(cost_model, actual, root.find(), ExprTree.make_node))
        == best_terms[-1]
    )
    expected = {
        "e0": {"a": [()], "/": [("e2", "e1")], "*": [("e0", "e4")]},
        "e1": {"2": [()]},
        "e2": {"*": [("e0", "e1")], "<<": [("e0", "e4")]},
        "e4": {"1": [()], "/": [("e1", "e1")]},
    }
    assert verify_egraph_shape(actual, expected)


def run_test():
    eg = EGraph(ExprTree(times_divide()))
    root = eg.root
    rules = make_rules()
    cost_model = ExprNodeCost()
    cost_analysis = MinimumCostExtractor()
    while True:
        version = eg.version
        print("BEST: ", cost_analysis.extract(cost_model, eg, root, ExprTree.make_node))
        Rule.apply_rules(rules, eg)
        if version == eg.version:
            break


if __name__ == "main":
    run_test()
