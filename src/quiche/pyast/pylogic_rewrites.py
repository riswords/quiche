from quiche.pyast import ASTQuicheTree

# X or False = X
or_False_rule = ASTQuicheTree.make_rule(
    "__quiche__x or False",
    "__quiche__x"
)

# X or True = True (only if X is effect-free)
or_True_rule = ASTQuicheTree.make_rule(
    "__quiche__x or True",
    "True"
)

# X or Y = Y or X (only if X and Y are effect-free)
or_commutativity_rule = ASTQuicheTree.make_rule(
    "__quiche__x or __quiche__y",
    "__quiche__y or __quiche__x"
)

# X or (Y or Z) = (X or Y) or Z
or_associativity_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x or (__quiche__y or __quiche__z)",
    "(__quiche__x or __quiche__y) or __quiche__z"
)

# X and False = False
and_False_rule = ASTQuicheTree.make_rule(
    "__quiche__x and False",
    "False"
)

# X and True = X
and_True_rule = ASTQuicheTree.make_rule(
    "__quiche__x and True",
    "__quiche__x"
)

# X and Y = Y and X (only if X and Y are effect-free)
and_commutativity_rule = ASTQuicheTree.make_rule(
    "__quiche__x and __quiche__y",
    "__quiche__y and __quiche__x"
)

# X and (Y and Z) = (X and Y) and Z
and_associativity_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x and (__quiche__y and __quiche__z)",
    "(__quiche__x and __quiche__y) and __quiche__z"
)

# (X and Y) or X = X (only if X and Y are effect-free)
and_or_elim_rule = ASTQuicheTree.make_rule(
    "(__quiche__x and __quiche__y) or __quiche__x",
    "__quiche__x"
)

# X and X = X (only if X is effect-free)
and_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x and __quiche__x",
    "__quiche__x"
)

# X or X = X (only if X is effect-free)
or_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x or __quiche__x",
    "__quiche__x"
)

# (X or Y) and Y = Y (only if X and Y are effect-free)
or_and_elim_rule = ASTQuicheTree.make_rule(
    "(__quiche__x or __quiche__y) and __quiche__y",
    "__quiche__y"
)

# TODO: (X or Y) and Z = (X or (Y and Z)) and Z (invertible) (is this logically true?)

# bool(X) = not (not X) (and note that not not op is faster than bool call)
bool_not_not_rule = ASTQuicheTree.make_rule(
    "bool(__quiche__x)",
    "not(not(__quiche__x))"
)


def get_all_logic_rules():
    """
    Logical rewrites for and, or, and not operators.
    WARNING: Many of these rules are unsound in the presence of side-effects, as
    they may reorder or eliminate expressions. At this time, Quiche doesn't check
    for effects, so callers are responsible for ensuring rules are soundly
    applied and for dealing with the fallout if they aren't. Use with caution.
    """
    from functools import reduce
    from operator import iconcat
    single_rules = [
        or_False_rule, or_True_rule, or_commutativity_rule, and_False_rule,
        and_True_rule, and_commutativity_rule, and_or_elim_rule, and_self_rule,
        or_self_rule, or_and_elim_rule,
    ]
    double_rules = [
        or_associativity_rules, and_associativity_rules,
    ]
    # results in "double" rules being at the end, after all single rules
    # (merely a comment on ordering, not a requirement)
    return reduce(iconcat, double_rules, single_rules)
