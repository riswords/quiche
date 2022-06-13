from quiche.quiche_tree import QuicheTree


class Rule:
    def __init__(self, lhs: QuicheTree, rhs: QuicheTree):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return "{} -> {}".format(self.lhs, self.rhs)
