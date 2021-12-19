from typing import NamedTuple, Tuple, Dict, List
from rewrite import Rule


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
        self.parent = top  # caching top
        return top


class ENode(NamedTuple):
    key: str
    args: Tuple[EClassID, ...]

    # def __init__(self, key, args):
    #    print('Creating enode ', key, ' with args: ', args)
    #    self.key = key
    #    self.args = args # EClassIDs?

    # def apply_substitution(self, subst) -> 'ENode':
    #    # returns ENode
    #    pass

    def canonicalize(self):
        # print("Canonize node: ", self.key, ", Canonize args: ", self.args)
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

    def is_saturated_or_timeout(self):
        pass

    def ematch(self, pattern: ENode, eclasses: Dict[EClassID, List[ENode]]):
        Env = Dict[str, EClassID]  # type alias
        """
        :param pattern: ENode
        :returns: List[Tuple[EClassID, Env]]
        """

        def match_in(p: ENode, eid: EClassID, env: Env):
            """
            :returns: Tuple[Bool, Env]
            """
            def enode_matches(p: ENode, e: ENode, env: Env):
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
                    env = {**env}  # expensive, but can be optimized (?)
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

        # because we merged eclasses, some enodes might now be the same,
        # meaning we can merge additional eclasses.
        new_uses = {}
        for enode, eclass in uses:
            enode = enode.canonicalize()
            if enode in new_uses:
                self.merge(eclass, new_uses[enode])
            new_uses[enode] = eclass.find()
        # note the find: it's possible that eclassid was merged, and uses
        # should be tied to the parent instead
        eclassid.find().uses += new_uses.items()

    def apply_rules(self, rules: List['Rule']):
        """
        :param rules: List[Rule]
        :returns: EGraph
        """
        canonical_eclasses = self.eclasses()

        matches = []
        for rule in rules:
            for eid, env in self.ematch(rule.lhs, canonical_eclasses):
                matches.append((rule, eid, env))
        print(f'VERSION {self.version}')
        for rule, eid, env in matches:
            new_eid = self.subst(rule.rhs, env)
            if eid is not new_eid:
                print(f'{eid} MATCHED {rule} with {env}')
            self.merge(eid, new_eid)
        self.rebuild()
        return self

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

    def subst(self, pattern: ENode, env: Dict[str, EClassID]):
        """
        :param pattern: ENode
        :param env: Dict[str, EClassID]
        :returns: EClassID
        """
        if not pattern.args and not isinstance(pattern.key, int):
            return env[pattern.key]
        else:
            enode = ENode(pattern.key,
                          tuple(self.subst(arg, env) for arg in pattern.args))
            return self.add(enode)
