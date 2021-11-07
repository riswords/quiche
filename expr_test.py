from typing import NamedTuple, Dict, Tuple, List
import math

from egraph import *
#from rewrite import Rule

class ExprNode(NamedTuple):
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

# Env = Dict[str, EClassID] # type alias
def ematch(eclasses: Dict[EClassID, List[ENode]], pattern: ExprNode):
    """
    :param eclasses: Dict[EClassID, List[ENode]]
    :param pattern: ExprNode
    :returns: List[Tuple[EClassID, Env]]
    """
    def match_in(p: ExprNode, eid: EClassID, env: 'Env'):
        """
        :returns: Tuple[Bool, Env]
        """
        def enode_matches(p: ExprNode, e:ENode, env: 'Env'):
            """
            :returns: Tuple[Bool, Env]
            """
            if enode.key != p.key:
                return False, env
            new_env = env
            for arg_pattern, arg_eid in zip(p.args, enode.args):
                matched, new_env = match_in(arg_pattern, arg_eid, new_env)
                if not matched:
                    return False, env
            return True, new_env
        if not p.args and not isinstance(p.key, int):
            # this is a leaf variable like x: match it with the env
            id = p.key
            if id not in env:
                env = {**env} # expensive, but can be optimized (?)
                env[id] = eid
                return True, env
            else:
                # check that this value matches the same thing (?)
                return env[id] is eid, env
        else:
            # does one of the ways to define this class match the pattern?
            for enode in eclasses[eid]:
                matches, new_env = enode_matches(p, enode, env)
                if matches:
                    return True, new_env
            return False, env
        
    matches = []
    for eid in eclasses.keys():
        match, env = match_in(pattern, eid, {})
        if match:
            matches.append((eid, env))
    return matches

def subst(eg: EGraph, pattern: ExprNode, env: Dict[str, EClassID]):
    """
    :param pattern: ExprNode
    :param env: Dict[str, EClassID]
    :returns: EClassID
    """
    if not pattern.args and not isinstance(pattern.key, int):
        return env[pattern.key]
    else:
        enode = ENode(pattern.key, tuple(subst(eg, arg, env) for arg in pattern.args))
        return eg.add(enode)

def apply_rules(eg: EGraph, rules: List['Rule']):
    """
    :param rules: List[Rule]
    :returns: EGraph
    """
    eclasses = eg.eclasses()
    matches = []
    for rule in rules:
        for eid, env in ematch(eclasses, rule.lhs):
            matches.append((rule, eid, env))
    print(f'VERSION {eg.version}')
    for rule, eid, env in matches:
        new_eid = subst(eg, rule.rhs, env)
        if eid is not new_eid:
            print(f'{eid} MATCHED {rule} with {env}')
        eg.merge(eid, new_eid)
    eg.rebuild()
    return eg

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
