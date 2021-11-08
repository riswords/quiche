from typing import NamedTuple, Optional, Tuple
from graphviz import Digraph

class EClassID:
    def __init__(self, id, parent: 'EClassID' = None):
        self.id = id
        self.parent = parent

        # List of tuples of (ENode, EClassID) of enodes that use this EClassID
        # and the EClassID of that use
        # Only set on a canonical EClass (parent == None) and is used in
        # `EGraph.rebuild()`
        self.uses = []
    
    def __repr__(self):
        return f'e{self.id}'
    
    def find(self):
        if self.parent is None:
            return self
        top = self.parent.find()
        self.parent = top # caching top
        return top

class ENode(NamedTuple):
    key: str
    args: Tuple[EClassID, ...]
    #
    #def __init__(self, key, args):
    #    print('Creating enode ', key, ' with args: ', args)
    #    self.key = key
    #    self.args = args # EClassIDs?
    
    #def apply_substitution(self, subst) -> 'ENode':
    #    # returns ENode
    #    pass
    
    def canonicalize(self):
        #print("Canonize node: ", self.key, ", Canonize args: ", self.args)
        return ENode(self.key, tuple(arg.find() for arg in self.args))



class EGraph:
    def __init__(self):
        self.id_counter = 0

        # quickly check whether the egraph has mutated
        self.version = 0

        # dict<ENode_canon, EClassID_noncanon> for checking if an enode is 
        # already defined
        self.hashcons = {}

        # List<EClassID> of eclasses mutated by a merge, used for `rebuild`
        self.worklist = []
    
    """def _repr_svg_(self):
        def format_record(x):
            if isinstance(x, list):
                return '{' + '|'.join(format_record(e) for e in x) + '}'
            else:
                return x
        
        def escape(x):
            return str(x).replace('<', '\<').replace('>', '\>')
        
        g = Digraph(node_attr={'shape': 'record', 'height': '.1'})
        for eclass, enodes in self.eclasses().items():
            g.node(f'{eclass.id}', label=f'e{eclass.id}', shape='circle')

            for enode in enodes:
                enode_id = str(id(enode))
                g.edge(f'{eclass.id}', enode_id)

                record = [escape(enode.key)]
                for i, arg in enumerate(enode.args):
                    g.edge(f'{enode_id}:p{i}', f'{arg.id}')
                    record.append(f'<p{i}>')
                g.node(enode_id, label='|'.join(record))
        
        return g._repr_svg_()"""

    def is_saturated_or_timeout(self):
        pass
    
    def ematch(self, lhs):
        pass
    
    def _new_singleton_eclass(self):
        singleton = EClassID(self.id_counter)
        self.id_counter += 1
        return singleton

    def add(self, enode: ENode):
        enode = enode.canonicalize()
        eclassid = self.hashcons.get(enode, None)
        if eclassid is None:
            # Node not found, so create it
            self.version += 1
            eclassid = self._new_singleton_eclass()
            for arg in enode.args:
                arg.uses.append((enode, eclassid))
        self.hashcons[enode] = eclassid
        # rhs of hashcons isn't canonicalized, so do that now
        return eclassid.find()
    
    def merge(self, eclass1, eclass2):
        e1 = eclass1.find()
        e2 = eclass2.find()
        if e1 is e2:
            return e1
        self.version += 1
        e1.parent = e2

        # Update uses of eclasses:
        # Maintain invariant that uses are recorded on the parent EClassID
        e2.uses += e1.uses
        e1.uses = None  # TODO: should be [] instead?

        # now that eclassid e2 is worklist, nodes in the hashcons may not be
        # canonicalized, and we might discover that 2 enodes are actually the
        # same value. We use `repair` to fix this and track in the `worklist`
        # list.
        self.worklist.append(e2)

    # Ensure we have a de-duplicated version of the EGraph    
    def rebuild(self):
        while self.worklist:
            # de-duplicate repeated calls to repair the same EClass
            todo = set(eid.find() for eid in self.worklist)
            self.worklist = []
            for eclassid in todo:
                self.repair(eclassid)
    
    def repair(self, eclassid):
        """
        Repair the EClassID `eclassid` by canonicalizing all nodes in the
        uses list.
        """
        assert eclassid.parent is None
        # reset uses of eclassid, repopulate at the end
        uses, eclassid.uses = eclassid.uses, []
        
        # any uses in hashcons may not be canoncial, so re-canonicalize them
        for enode, eclass in uses:
            if enode in self.hashcons:
                del self.hashcons[enode]
            enode = enode.canonicalize()
            self.hashcons[enode] = eclass.find()
        
        # because we merged eclasses, some enodes might now be the same, meaning
        # we can merge additional eclasses.
        new_uses = {}
        for enode, eclass in uses:
            enode = enode.canonicalize()
            if enode in new_uses:
                self.merge(eclass, new_uses[enode])
            new_uses[enode] = eclass.find()
        #note the find: it's possible that eclassid was merged, and uses should
        # be tied to the parent instead
        eclassid.find().uses += new_uses.items()
    
    
    def extract_best(self):
        pass


    def eclasses(self):
        """
        Extract dictionary of (canonicalized) EClassIDs to ENodes
        :returns: Dict[EClassID, List[ENode]]
        """
        result = {}
        for enode, eid in self.hashcons.items():
            eid = eid.find()
            if eid not in result:
                result[eid] = [enode]
            else:
                result[eid].append(enode)
        return result
    
    #def add_expr_node(self, node: 'ExprNode'):
    #    return self.add(ENode(node.key, tuple(self.add_expr_node(n) for n in node.args)))
