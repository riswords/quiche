from quiche.egraph import ENode, EGraph, EClassID
from quiche.rewrite import Rule

class PropNode(ENode):
    key: "Union[str, int]"  # use int to represent int literals,
    args: "Tuple[PropNode,...]"

    
    @classmethod
    def parse(cls, data):
        parser = PropParser()
        parser.build()
        result = parser.parse(data)
        return result


    # print it out like an s-expr
    def __repr__(self):
        if self.args:
            return f'({self.key} {" ".join(str(arg) for arg in self.args)})'
        else:
            return str(self.key)

    @staticmethod
    def make_rule(lhs, rhs):
        return Rule(PropNode.parse(lhs), PropNode.parse(rhs))