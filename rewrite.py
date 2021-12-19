

class Rule:
    # TODO: remove ExprNode dependency
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return '{} -> {}'.format(self.lhs, self.rhs)
