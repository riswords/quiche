from egraph import ENode, EClassID

from expr_test import ExprNode

class Rule:

    def __init__(self, fn):
        self.lhs, self.rhs = self.exp(fn)

    def __repr__(self):
        return '{} -> {}'.format(self.lhs, self.rhs)
    
    def exp(self, fn):
        c = fn.__code__
        args = [ExprNode(c.co_varnames[i], ()) for i in range(c.co_argcount)]
        return fn(*args)