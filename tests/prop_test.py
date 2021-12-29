from quiche.egraph import EGraph

from .prop_test_parser import PropParser, PropNode, PropNodeCost, PropNodeExtractor

from .test_egraph import verify_egraph_shape, print_egraph


def make_rules():
    rules = [
        # x -> y ===> ~x | y
        PropNode.make_rule("(-> x y)", "(| (~ x) y)"),
        # ~x | y ===> x -> y
        PropNode.make_rule("(| (~ x) y)", "(-> x y)"),
        # x ===> ~ (~x)
        PropNode.make_rule("x", "~ (~ x)"),
        # x | y ===> y | x
        PropNode.make_rule("(| x y)", "(| y x)"),
    ]
    return rules


def x_implies_y():
    test_str = "(-> x y)"
    parser = PropParser()
    parser.build()
    return parser.parse(test_str)


def not_x_or_y():
    test_str = "(| (~ x) y)"
    parser = PropParser()
    parser.build()
    return parser.parse(test_str)


def not_y_implies_not_x():
    test_str = "(-> (~ y) (~ x))"
    parser = PropParser()
    parser.build()
    return parser.parse(test_str)


def test_implies():
    """Test building egraph of x -> y"""
    tree = x_implies_y()

    actual = EGraph()
    actual.from_tree(tree)

    expected = {"e0": {"x": []}, "e1": {"y": []}, "e2": {"->": ["e0", "e1"]}}
    assert verify_egraph_shape(actual, expected)


def test_nor():
    """Test building egraph of ~x | y"""
    tree = not_x_or_y()
    actual = EGraph()
    actual.from_tree(tree)

    expected = {
        "e0": {"x": []},
        "e1": {"~": ["e0"]},
        "e2": {"y": []},
        "e3": {"|": ["e1", "e2"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_add_implies_and_nor():
    """Test building egraph of both props: x -> y and ~x | y"""
    actual = EGraph()
    actual.from_tree(x_implies_y())
    actual.from_tree(not_x_or_y())
    actual.rebuild()

    expected = {
        "e0": {"x": []},
        "e1": {"y": []},
        "e2": {"->": ["e0", "e1"]},
        "e3": {"~": ["e0"]},
        "e4": {"|": ["e3", "e1"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_and_or_not_implies():
    test_str = "(& (-> x y) (-> (~ x) z))"
    parser = PropParser()
    parser.build()
    tree = parser.parse(test_str)

    actual = EGraph()
    actual.from_tree(tree)

    expected = {
        "e0": {"x": []},
        "e1": {"y": []},
        "e2": {"->": ["e0", "e1"]},
        "e3": {"~": ["e0"]},
        "e4": {"z": []},
        "e5": {"->": ["e3", "e4"]},
        "e6": {"&": ["e2", "e5"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_merge_props():
    actual = EGraph()
    impl_root = actual.from_tree(x_implies_y())
    nor_root = actual.from_tree(not_x_or_y())
    actual.merge(impl_root, nor_root)
    actual.rebuild()

    expected = {
        "e0": {"x": []},
        "e1": {"y": []},
        "e4": {"->": ["e0", "e1"], "|": ["e3", "e1"]},
        "e3": {"~": ["e0"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_prop_ematch():
    """Test rewriting (a & b) -> c to ~(a & b) | c"""
    test_str = "(-> (& a b) c)"
    parser = PropParser()
    parser.build()
    tree = parser.parse(test_str)

    actual = EGraph()
    _ = actual.from_tree(tree)

    # Verify tree shape
    expected = {
        "e0": {"a": []},
        "e1": {"b": []},
        "e2": {"&": ["e0", "e1"]},
        "e3": {"c": []},
        "e4": {"->": ["e2", "e3"]},
    }
    assert verify_egraph_shape(actual, expected)

    # Rule to rewrite x -> y to ~x | y
    rule = PropNode.make_rule("(-> x y)", "(| (~ x) y)")
    matches = actual.ematch(rule.lhs, actual.eclasses())

    # expect exactly one match
    assert len(matches) == 1
    match = matches[0]

    # expect match to be (e4, {x: e2, b: e3})
    assert len(match) == 2
    assert str(match[0]) == "e4"

    assert len(match[1]) == 2
    assert str(match[1]["x"]) == "e2"
    assert str(match[1]["y"]) == "e3"


def test_expr_subst():
    actual = EGraph()
    impl_root = actual.from_tree(x_implies_y())
    nor_root = actual.from_tree(not_x_or_y())
    actual.merge(impl_root, nor_root)
    actual.rebuild()

    # x -> y <===> ~x | y
    rule = PropNode.make_rule("(-> x y)", "(| (~ x) y)")
    matches = actual.ematch(rule.lhs, actual.eclasses())
    lhs, env = matches[0]
    rhs = actual.subst(rule.rhs, env)

    assert str(rhs) == "e4"
    expected = {
        "e0": {"x": []},
        "e1": {"y": []},
        "e3": {"~": ["e0"]},
        "e4": {"|": ["e3", "e1"], "->": ["e0", "e1"]},
    }
    verify_egraph_shape(actual, expected)


def test_apply_rules_for_contrapositive():
    actual = EGraph()
    _ = actual.from_tree(x_implies_y())
    rules = make_rules()
    versions = [3, 14, 16]
    for version in versions:
        assert actual.version == version
        actual.apply_rules(rules)
    assert actual.version == versions[-1]
    # print_egraph(actual)
    expected = {
        "e3": {"~": ["e5"]},
        "e5": {"x": [], "~": ["e3"]},
        "e6": {"~": ["e7"]},
        "e7": {"y": [], "~": ["e6"]},
        "e8": {"~": ["e10"]},
        "e10": {"~": ["e8"], "->": ["e5", "e7"], "|": ["e3", "e7"], "|": ["e7", "e3"]},
    }
    assert verify_egraph_shape(actual, expected)


def test_schedule_contrapositive():
    # Verify rule application
    actual = EGraph()
    root = actual.from_tree(not_y_implies_not_x())
    rules = make_rules()
    versions = [5, 18, 20]
    best_terms = ["(-> (~ y) (~ x))", "(| y (~ x))", "(| y (~ x))", "(| y (~ x))"]
    for version, term in zip(versions, best_terms):
        assert actual.version == version
        # Verify schedule-extracted term is correct
        cost_model = PropNodeCost()
        cost_analysis = PropNodeExtractor(cost_model)
        extracted = cost_analysis.schedule(actual, root)
        assert str(extracted) == term
        actual.apply_rules(rules)
    assert actual.version == versions[-1]
    assert str(cost_analysis.schedule(actual, root)) == best_terms[-1]

    # print_egraph(actual)
    expected = {
        "e5": {"y": [], "~": ["e7"]},
        "e7": {"~": ["e5"]},
        "e8": {"x": [], "~": ["e9"]},
        "e9": {"~": ["e8"]},
        "e10": {"~": ["e12"]},
        "e12": {
            "~": ["e10"],
            "|": ["e5", "e9"],
            "->": ["e7", "e9"],
            "|": ["e9", "e5"],
        },
    }
    assert verify_egraph_shape(actual, expected)
