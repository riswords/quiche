from egraph import *
from expr_test import *
from rewrite import Rule

def exp(fn):
    c = fn.__code__
    args = [ExprNode(c.co_varnames[i], ()) for i in range(c.co_argcount)]
    return fn(*args)

def add_expr_node(egraph: EGraph, node: ExprNode):
    return egraph.add(ENode(node.key, tuple(add_expr_node(egraph, n) for n in node.args)))

def make_rules():
    rules = [
        Rule(lambda x: (x * 2, x << 1)) # mult by 2 is shift left 1
        , Rule(lambda x, y, z: ((x * y) / z, x * (y / z))) # reassociate *,/
        , Rule(lambda x: (x / x, ExprNode(1, ()))) # x/x = 1
        , Rule(lambda x: (x * 1, x)) # simplify mult by 1
    ]
    return rules

def times_divide():
    return exp(lambda a: (a * 2) / 2)

def shift():
    return exp(lambda a: a << 1)

def times2():
    return exp(lambda a: a * 2)

def print_egraph(eg):
    for eid, enode in eg.eclasses().items():
        print(eid,  ': ', [en.key for en in enode], ' ; ', [en.args for en in enode])

def run_test():
    eg = EGraph()
    root = add_expr_node(eg, times_divide())
    rules = make_rules()
    while True:
        version = eg.version
        print('BEST: ', schedule(eg, root))
        apply_rules(eg, rules)
        if version == eg.version:
            break

if __name__ == 'main':
    run_test()
    