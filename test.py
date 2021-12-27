from typing import Dict, List

from egraph import EGraph, ENode
from expr_test import ExprNode, ExprNodeCost, ExprNodeExtractor
from rewrite import Rule


def exp(fn):
    c = fn.__code__
    args = [ExprNode(c.co_varnames[i], ()) for i in range(c.co_argcount)]
    return fn(*args)


def add_expr_node(egraph: EGraph, node: ExprNode):
    return egraph.add(
        ENode(node.key, tuple(add_expr_node(egraph, n) for n in node.args))
    )


def make_rules():
    rules = [
        Rule(lambda x: (x * 2, x << 1)),  # mult by 2 is shift left 1
        Rule(lambda x, y, z: ((x * y) / z, x * (y / z))),  # reassociate *,/
        Rule(lambda x: (x / x, ExprNode(1, ()))),  # x/x = 1
        Rule(lambda x: (x * 1, x)),  # simplify mult by 1
    ]
    return rules


def times_divide():
    return exp(lambda a: (a * 2) / 2)


def shift():
    return exp(lambda a: a << 1)


def times2():
    return exp(lambda a: a * 2)


def print_egraph(eg):
    for eid, enode in eg.eclasses().items():
        print(eid, ": ", [en.key for en in enode], " ; ", [en.args for en in enode])


def verify_egraph_shape(
    actual_egraph: EGraph, expected_shape: Dict[str, Dict[str, List[str]]]
):
    eclasses = actual_egraph.eclasses()
    # assert len(eclasses) == len(expected_shape)
    for eclassid, eclass in eclasses.items():
        actual_eclassid = str(eclassid)
        assert actual_eclassid in expected_shape
        for enode in eclass:
            actual_key = str(enode.key)
            assert actual_key in expected_shape[actual_eclassid]
            for arg in enode.args:
                assert str(arg) in expected_shape[actual_eclassid][actual_key]
    return True


def test_add_times_divide():
    actual = EGraph()
    _ = add_expr_node(actual, times_divide())
    expected = {
        "e0": {"a": []},
        "e1": {"2": []},
        "e2": {"*": ["e0", "e1"]},
        "e3": {"/": ["e2", "e1"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_add_shift():
    actual = EGraph()
    _ = add_expr_node(actual, shift())
    expected = {
        "e0": {"a": []},
        "e1": {"1": []},
        "e2": {"<<": ["e0", "e1"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_add_two_exprs():
    actual = EGraph()
    _ = add_expr_node(actual, times_divide())
    _ = add_expr_node(actual, shift())
    expected = {
        "e0": {"a": []},
        "e1": {"2": []},
        "e2": {"*": ["e0", "e1"]},
        "e3": {"/": ["e2", "e1"]},
        "e4": {"1": []},
        "e5": {"<<": ["e0", "e4"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_merge_exprs():
    actual = EGraph()
    _ = add_expr_node(actual, times_divide())
    times_root = add_expr_node(actual, times2())
    shift_root = add_expr_node(actual, shift())
    actual.merge(times_root, shift_root)
    actual.rebuild()

    expected = {
        "e0": {"a": []},
        "e1": {"2": []},
        "e3": {"/": ["e5", "e1"]},
        "e4": {"1": []},
        "e5": {"<<": ["e0", "e4"], "*": ["e0", "e1"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_expr_ematch():
    actual = EGraph()
    _ = add_expr_node(actual, times_divide())
    # Rule to reassociate *,/
    rule = ExprNode.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z)))
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
    actual = EGraph()
    _ = add_expr_node(actual, times_divide())
    shift_root = add_expr_node(actual, shift())
    times2_root = add_expr_node(actual, times2())
    actual.merge(times2_root, shift_root)
    actual.rebuild()
    # Rule to reassociate *,/
    rule = ExprNode.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z)))
    matches = actual.ematch(rule.lhs, actual.eclasses())
    lhs, env = matches[0]
    rhs = actual.subst(rule.rhs, env)

    assert str(rhs) == "e7"
    expected = {
        "e0": {"a": []},
        "e1": {"2": []},
        "e3": {"/": ["e5", "e1"]},
        "e4": {"1": []},
        "e5": {"<<": ["e0", "e4"], "*": ["e0", "e1"]},
        "e6": {"/": ["e1", "e1"]},
        "e7": {"*": ["e0", "e6"]},
    }
    verify_egraph_shape(actual, expected)


def test_apply_rules():
    actual = EGraph()
    _ = add_expr_node(actual, times_divide())
    rules = [
        # Multiply x by 2 === shift x left by 1
        ExprNode.make_rule(lambda x: (x * 2, x << 1)),
        # Reassociate *,/
        ExprNode.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z))),
        # x/x = 1
        ExprNode.make_rule(lambda x: (x / x, ExprNode(1, ()))),
        # Simplify x * 1 === x
        ExprNode.make_rule(lambda x: (x * 1, x)),
    ]
    versions = [4, 10, 11, 12]
    for version in versions:
        assert actual.version == version
        actual.apply_rules(rules)
    assert actual.version == versions[-1]
    expected = {
        "e0": {"a": [], "/": ["e5", "e1"], "*": ["e0", "e4"]},
        "e1": {"2": []},
        "e4": {"1": [], "/": ["e1", "e1"]},
        "e5": {"*": ["e0", "e1"], "<<": ["e0", "e4"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_schedule():
    # Verify rule application
    actual = EGraph()
    root = add_expr_node(actual, times_divide())
    rules = [
        # Multiply x by 2 === shift x left by 1
        ExprNode.make_rule(lambda x: (x * 2, x << 1)),
        # Reassociate *,/
        ExprNode.make_rule(lambda x, y, z: ((x * y) / z, x * (y / z))),
        # x/x = 1
        ExprNode.make_rule(lambda x: (x / x, ExprNode(1, ()))),
        # Simplify x * 1 === x
        ExprNode.make_rule(lambda x: (x * 1, x)),
    ]
    versions = [4, 10, 11, 12]
    best_terms = ["(/ (* a 2) 2)", "(/ (<< a 1) 2)", "(* a 1)", "a"]
    for version, term in zip(versions, best_terms):
        assert actual.version == version
        # Verify schedule-extracted term is correct
        cost_model = ExprNodeCost()
        cost_analysis = ExprNodeExtractor(cost_model)
        extracted = cost_analysis.schedule(actual, root)
        assert str(extracted) == term
        actual.apply_rules(rules)
    assert actual.version == versions[-1]
    assert str(cost_analysis.schedule(actual, root)) == best_terms[-1]
    expected = {
        "e0": {"a": [], "/": ["e5", "e1"], "*": ["e0", "e4"]},
        "e1": {"2": []},
        "e4": {"1": [], "/": ["e1", "e1"]},
        "e5": {"*": ["e0", "e1"], "<<": ["e0", "e4"]},
    }
    assert verify_egraph_shape(actual, expected)


def run_test():
    eg = EGraph()
    root = add_expr_node(eg, times_divide())
    rules = make_rules()
    cost_model = ExprNodeCost()
    cost_analysis = ExprNodeExtractor(cost_model)
    while True:
        version = eg.version
        print("BEST: ", cost_analysis.schedule(eg, root))
        eg.apply_rules(rules)
        if version == eg.version:
            break


if __name__ == "main":
    run_test()
