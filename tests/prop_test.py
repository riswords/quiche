from quiche.egraph import ENode, EGraph, EClassID
from quiche.rewrite import Rule

from .prop_test_lexer import PropLexer
from .prop_test_parser import PropParser, PropNode

from .test_egraph import verify_egraph_shape

def make_rules():
    rules = [
        # a -> b <===> ~a | b
        PropNode.make_rule("(-> x y)", "(| (~ a) b)"),
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

def test_implies():
    """ Test building egraph of x -> y"""
    tree = x_implies_y()
    
    actual = EGraph()
    actual.from_tree(tree)

    expected = {
        "e0": { "x": [] },
        "e1": { "y": [] },
        "e2": { "->": ["e0", "e1"] }
    }
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
        "e3": {"|": ["e1", "e2"]}
    }
    assert verify_egraph_shape(actual, expected)

def test_add_implies_and_nor():
    """ Test building egraph of both props: x -> y and ~x | y"""
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
        "e0": { "x": [] },
        "e1": { "y": [] },
        "e2": { "->": ["e0", "e1"] },
        "e3": { "~": ["e0"] },
        "e4": { "z": [] },
        "e5": { "->": ["e3", "e4"] },
        "e6": { "&": ["e2", "e5"] }
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
        "e4": {
            "->": ["e0", "e1"],
            "|": ["e3", "e1"]
        },
        "e3": {"~": ["e0"]},
    }
    assert verify_egraph_shape(actual, expected)

def test_prop_ematch():
    actual = EGraph()
    _ = actual.from_tree(x_implies_y())
    # Rule to rewrite a->b to ~a|b
    rule = PropNode.make_rule("(-> a b)", "(| (~ a) b)")
    matches = actual.ematch(rule.lhs, actual.eclasses())

    # expect exactly one match
    assert len(matches) == 1
    match = matches[0]

    # expect match to be (e2, {a: e0, b: e1})
    assert len(match) == 2
    assert str(match[0]) == "e2"

    assert len(match[1]) == 2
    assert str(match[1]["a"]) == "e0"
    assert str(match[1]["b"]) == "e1"


if __name__ == "main":
    result = test()
    
