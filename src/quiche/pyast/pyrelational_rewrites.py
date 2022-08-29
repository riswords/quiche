from quiche.pyast import ASTQuicheTree

# X < Y = Y > X
lt_gt_symmetry_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x < __quiche__y",
    "__quiche__y > __quiche__x"
)

# X <= Y = Y >= X
lte_gte_symmetry_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x <= __quiche__y",
    "__quiche__y >= __quiche__x"
)

# Skipping Peggy property-based relational/arithmetic rules

# X < X = False
lt_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x < __quiche__x",
    "False"
)

# X > X = False
gt_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x > __quiche__x",
    "False"
)

# X != X = False
ne_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x != __quiche__x",
    "False"
)

# X == X = True
eq_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x == __quiche__x",
    "True"
)

# X >= X = True
gte_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x >= __quiche__x",
    "True"
)

# X <= X = True
lte_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x <= __quiche__x",
    "True"
)

# not (X > Y) = X <= Y
not_gt_rule = ASTQuicheTree.make_rule(
    "not (__quiche__x > __quiche__y)",
    "__quiche__x <= __quiche__y"
)

# not (X < Y) = X >= Y
not_lt_rule = ASTQuicheTree.make_rule(
    "not (__quiche__x < __quiche__y)",
    "__quiche__x >= __quiche__y"
)


def get_all_relational_rules():
    from functools import reduce
    from operator import iconcat
    single_rules = [
        lt_self_rule, gt_self_rule, ne_self_rule, eq_self_rule, gte_self_rule,
        lte_self_rule, not_gt_rule, not_lt_rule
    ]
    double_rules = [
        lt_gt_symmetry_rules, lte_gte_symmetry_rules,
    ]
    # results in "double" rules being at the end, after all single rules
    # (merely a comment on ordering, not a requirement)
    return reduce(iconcat, double_rules, single_rules)
