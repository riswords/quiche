from quiche.pyast import ASTQuicheTree

# X xor 0 = X
xor_zero_rule = ASTQuicheTree.make_rule(
    "__quiche__x ^ 0",
    "__quiche__x"
)

# X xor Y = Y xor X
xor_commutativity_rule = ASTQuicheTree.make_rule(
    "__quiche__x ^ __quiche__y",
    "__quiche__y ^ __quiche__x"
)

# X xor (Y xor Z) = (X xor Y) xor Z
xor_associativity_rules = ASTQuicheTree.make_invertible_rules(
    "__quiche__x ^ (__quiche__y ^ __quiche__z)",
    "(__quiche__x ^ __quiche__y) ^ __quiche__z"
)

# TODO: Add these rules
# X | 0 = X
# X | Y = Y | X
# X | (Y | Z) = (X | Y) | Z
# X & 0 = 0
# X & Y = Y & X
# X & (Y & Z) = (X & Y) & Z (invertible)
# (X & Y) ^ (X | Y) = X ^ Y
# (X & Y) ^ (X & Z) = (Y ^ Z) & X
# (X & Y) | X = X
# (X << C1) * C2 = X * (C2 << C1)
# X & X = X
# X | X = X
# (X ^ C1) & C2 = (X & C1) ^ (C1 & C2) (invertible)
# (X | C) & C = C
# (X || C1) && C2 = (X || (C1 && C2)) && C2
# ~~X = X


def get_all_bitwise_rules():
    from functools import reduce
    from operator import iconcat
    single_rules = [
        xor_zero_rule, xor_commutativity_rule,
    ]
    double_rules = [
        xor_associativity_rules,
    ]
    # results in "double" rules being at the end, after all single rules
    # (merely a comment on ordering, not a requirement)
    return reduce(iconcat, double_rules, single_rules)
