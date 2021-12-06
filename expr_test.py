from typing import NamedTuple, Dict, Tuple, List
import math

from egraph import *
#from rewrite import Rule

class ExprNode(ENode):
    key: 'Either[str, int]' # use int to represent int literals,
    args: 'Tuple[ExprNode,...]'

    # overload some operators to allow us to easily construct these
    def _mk_op(key):
        return lambda *args: ExprNode(key, tuple(arg if isinstance(arg, ExprNode) else ExprNode(arg, ()) for arg in args))

    __add__ = _mk_op('+')
    __mul__ = _mk_op('*')
    __lshift__ = _mk_op('<<')
    __truediv__ = _mk_op('/')
  
    # print it out like an s-expr
    def __repr__(self):
        if self.args:
            return f'({self.key} {" ".join(str(arg) for arg in self.args)})'
        else:
            return str(self.key)

expr_costs = {
      '+': 1
    , '<<': 1
    , '*': 2
    , '/': 3    
}

def schedule(eg: EGraph, result: EClassID):
    """
    Extract lowest cost expression from EGraph.
    Calculate lowest cost for each node using `expr_costs` to weight each operation.
    :returns: ExprNode for the expression with the lowest cost
    """
    result = result.find()
    eclasses = eg.eclasses()
    # costs is Dict[EClassID, Tuple[int, ENode]]
    costs = {eid: (math.inf, None) for eid in eclasses.keys()}
    changed = True

    def enode_cost(enode: ENode):
        return expr_costs.get(enode.key, 0) + sum(costs[eid][0] for eid in enode.args)
    
    # iterate until saturation, taking lowest cost option
    while changed:
        changed = False
        for eclass, enodes in eclasses.items():
            new_cost = min((enode_cost(enode), enode) for enode in enodes)
            if costs[eclass][0] != new_cost[0]:
                changed = True
            costs[eclass] = new_cost
    
    def extract(eid):
        enode = costs[eid][1]
        return ExprNode(enode.key, tuple(extract(arg) for arg in enode.args))
    
    return extract(result)
