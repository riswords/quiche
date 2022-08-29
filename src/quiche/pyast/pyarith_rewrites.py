from ast import Constant, Num

from quiche.pyast import ASTQuicheTree

# X * 0 = 0
mul_zero_rule = ASTQuicheTree.make_rule(
    "__quiche__x * 0",
    "0"
)

# X / 1 = X
div_one_rule = ASTQuicheTree.make_rule(
    "__quiche__x / 1",
    "__quiche__x"
)

# X / X = 1
div_self_rule = ASTQuicheTree.make_conditional_rule(
    "__quiche__x / __quiche__x",
    "1",
    lambda eg, eid, env:
        not any([(not enode.args) and enode.key in [("int", Constant, 0, None), ("int", Num, 0)] for enode in eg.lookup_eclass(eg.env_lookup(env, "__quiche__x"))])
)

# X * 1 = X
mul_one_rule = ASTQuicheTree.make_rule(
    "__quiche__x * 1",
    "__quiche__x"
)

# X + 0 = X
add_zero_rule = ASTQuicheTree.make_rule(
    "__quiche__x + 0",
    "__quiche__x"
)

# X - 0 = X
sub_zero_rule = ASTQuicheTree.make_rule(
    "__quiche__x - 0",
    "__quiche__x"
)

# X - X = 0
sub_self_rule = ASTQuicheTree.make_rule(
    "__quiche__x - __quiche__x",
    "0"
)

# X * Y = Y * X
mul_commutativity_rule = ASTQuicheTree.make_rule(
    "__quiche__x * __quiche__y",
    "__quiche__y * __quiche__x"
)

# X + Y = Y + X
add_commutativity_rule = ASTQuicheTree.make_rule(
    "__quiche__x + __quiche__y",
    "__quiche__y + __quiche__x"
)

# X * (Y + Z) = (X * Y) + (X * Z)
mul_distributivity_over_add_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x * (__quiche__y + __quiche__z)",
    "(__quiche__x * __quiche__y) + (__quiche__x * __quiche__z)"
)

# X * (Y - Z) = (X * Y) - (X * Z)
mul_distributivity_over_sub_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x * (__quiche__y - __quiche__z)",
    "(__quiche__x * __quiche__y) - (__quiche__x * __quiche__z)"
)

# X + (Y + Z) = (X + Y) + Z
add_associativity_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x + (__quiche__y + __quiche__z)",
    "(__quiche__x + __quiche__y) + __quiche__z"
)


# Skipping Peggy property-based relational/arithmetic rules
# Skipping shift rules for now

# X - (Y + Z) = (X - Y) - Z
sub_add_ordering_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x - (__quiche__y + __quiche__z)",
    "(__quiche__x - __quiche__y) - __quiche__z"
)

# X - (Y - Z) = (X - Y) + Z
sub_sub_ordering_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x - (__quiche__y - __quiche__z)",
    "(__quiche__x - __quiche__y) + __quiche__z"
)

# (X + Y) - Z = X + (Y - Z)
add_sub_ordering_rules = ASTQuicheTree.make_invertible_rules(
    "(__quiche__x + __quiche__y) - __quiche__z",
    "__quiche__x + (__quiche__y - __quiche__z)"
)

# Not from Peggy, but still reasonable
# X * Y * Z = X * (Y * Z)
mul_associativity_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x * __quiche__y * __quiche__z",
    "__quiche__x * (__quiche__y * __quiche__z)")

# Also not from Peggy
# NOTE: doesn't need a div 0 check because if either Y or Z is 0
# the error is preserved
# X / Y / Z = X / (Y * Z)
mul_div_ordering_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x / __quiche__y / __quiche__z",
    "__quiche__x / (__quiche__y * __quiche__z)")


# Not from Peggy, but for classic egg example:
# NOTE: doesn't need a div 0 check because the denominator is preserved
# (X * Y) / Z = (X / Z) * (Y / Z)
mul_div_distributive_rule = ASTQuicheTree.make_rule(
    "(__quiche__x * __quiche__y) / __quiche__z",
    "(__quiche__x / __quiche__z) * (__quiche__y / __quiche__z)")


def get_all_arith_rules():
    from functools import reduce
    from operator import iconcat
    single_rules = [
        mul_zero_rule, div_one_rule, div_self_rule, mul_one_rule, add_zero_rule,
        sub_zero_rule, sub_self_rule, mul_commutativity_rule,
        add_commutativity_rule, mul_div_distributive_rule
    ]
    double_rules = [
        mul_distributivity_over_add_rules, mul_distributivity_over_sub_rules,
        add_associativity_rules,
        sub_add_ordering_rules, sub_sub_ordering_rules, add_sub_ordering_rules,
        mul_associativity_rules, mul_div_ordering_rules

    ]
    # results in "double" rules being at the end, after all single rules
    # (merely a comment on ordering, not a requirement)
    return reduce(iconcat, double_rules, single_rules)
