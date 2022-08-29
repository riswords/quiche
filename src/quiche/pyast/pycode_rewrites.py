from quiche.pyast import ASTQuicheTree

# Assignment collapse
# x = 1;
# y = 2;
# May be rewritten as:
# x, y = 1, 2
# When x does not occur in the RHS of the assignment to y, or more generally, when none of the targets
# of the first assignment occur in the RHS of the second assignment.
or_False_rule = ASTQuicheTree.make_rule(
    "__quiche__x or False",
    "__quiche__x"
)

# X or (Y or Z) = (X or Y) or Z
or_associativity_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x or (__quiche__y or __quiche__z)",
    "(__quiche__x or __quiche__y) or __quiche__z"
)


def get_all_code_rules():
    """
    Special rewrites for Python code.
    WARNING: Some of these rules may be unsound in the presence of side-effects, as
    they may reorder or eliminate expressions. At this time, Quiche doesn't check
    for effects, so callers are responsible for ensuring rules are soundly
    applied and for dealing with the fallout if they aren't. Use with caution.
    """
    from functools import reduce
    from operator import iconcat
    single_rules = [
        or_False_rule
    ]
    double_rules = [
        or_associativity_rules
    ]
    # results in "double" rules being at the end, after all single rules
    # (merely a comment on ordering, not a requirement)
    return reduce(iconcat, double_rules, single_rules)
