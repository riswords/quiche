from typing import NamedTuple, Tuple, Dict, List, Any

from .quiche_tree import QuicheTree
from .rewrite import Rule


class EClassID:
    def __init__(self, id, parent: "EClassID" = None):
        self.id = id
        self.parent = parent

        # List of tuples of (ENode, EClassID) of enodes that use this EClassID
        # and the EClassID of that use
        # Only set on a canonical EClass (parent == None) and is used in
        # `EGraph.rebuild()`
        self.uses: List[Tuple[ENode, EClassID]] = []

    def __repr__(self):
        return f"e{self.id}"

    # TODO: This is a hack to make min work properly in term extraction
    # because otherwise if we have a tie, we get an error about
    # EClassIDs not being comparable.
    def __lt__(self, other):
        return self.id < other.id

    def __le__(self, other):
        return self.id <= other.id

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __ne__(self, other):
        return self.id != other.id

    def __gt__(self, other):
        return self.id > other.id

    def __ge__(self, other):
        return self.id >= other.id

    # end TODO

    def find(self):
        if self.parent is None:
            return self
        top = self.parent.find()
        self.parent = top  # caching top
        return top


class ENode(NamedTuple):
    key: Any
    args: Tuple[EClassID, ...]

    # def __init__(self, key, args):
    #    print('Creating enode ', key, ' with args: ', args)
    #    self.key = key
    #    self.args = args # EClassIDs?

    # def apply_substitution(self, subst) -> 'ENode':
    #    # returns ENode
    #    pass

    # print it out like an s-expr
    def __repr__(self):
        if self.args:
            return f'({self.key} {" ".join(str(arg) for arg in self.args)})'
        else:
            return str(self.key)

    def canonicalize(self):
        # print("Canonize node: ", self.key, ", Canonize args: ", self.args)
        return ENode(self.key, tuple(arg.find() for arg in self.args))


class EGraph:
    def __init__(self, tree: QuicheTree = None):
        self.id_counter = 0

        # quickly check whether the egraph has mutated
        self.version = 0

        # dict<ENode_canon, EClassID_noncanon> for checking if an enode is
        # already defined
        self.hashcons: Dict[ENode, EClassID] = {}

        # List<EClassID> of eclasses mutated by a merge, used for `rebuild`
        self.worklist: List[EClassID] = []

        self.root = None
        if tree is not None:
            self.root = self.add(tree)

    def _repr_svg_(self):
        from graphviz import Digraph

        def format_record(x):
            if isinstance(x, list):
                return '{' + '|'.join(format_record(e) for e in x) + '}'
            else:
                return x

        def escape(x):
            escapes = [('|', '\\|'),
                       ('<', '\\<'),
                       ('>', '\\>')]
            x = str(x)
            for old, new in escapes:
                x = x.replace(old, new)
            # return str(x).replace('|', '\\|').replace('<', '\\<').replace('>', '\\>')
            return x

        graph = Digraph(node_attr={'shape': 'record', 'height': '.1'})
        for eclass, enodes in self.eclasses().items():
            graph.node(f'{eclass.id}', label=f'e{eclass.id}', shape='circle')

            for enode in enodes:
                enode_id = str(id(enode))
                graph.edge(f'{eclass.id}', enode_id)

                record = [escape(enode.key)]
                for i, arg in enumerate(enode.args):
                    graph.edge(f'{enode_id}:p{i}', f'{arg.id}')
                    record.append(f'<p{i}>')
                graph.node(enode_id, label='|'.join(record))
        return graph._repr_image_svg_xml()

    def write_to_svg(self, filename: str):
        """
        Write e-graph to file in SVG format.

        :param filename: filename to write
        :return: None
        """
        svg_xml = self._repr_svg_()
        with open(filename, "w") as f:
            f.write(svg_xml)

    def is_saturated_or_timeout(self):
        pass

    def ematch(self, pattern: QuicheTree, eclasses: Dict[EClassID, List[ENode]]):
        Env = Dict[str, EClassID]  # type alias
        """
        :param pattern: QuicheTree
        :param eclasses: Dict[EClassID, List[ENode]]
        :returns: List[Tuple[EClassID, Env]]
        """

        def match_in(
            p: QuicheTree, eid: EClassID, envs: List[Env]
        ) -> Tuple[bool, List[Env]]:
            """
            :param p: QuicheTree
            :param eid: EClassID
            :param envs: List[Env]
            :returns: Tuple[bool, List[Env]]
            """

            def enode_matches(p: QuicheTree, e: ENode, envs: List[Env]):
                """
                :returns: Tuple[Bool, List[Env]]
                """
                if e.key != p.value():
                    return False, envs
                    # return False, []

                matched = False
                matched_envs = []
                for env in envs:
                    matched_env, new_envs = enode_matches_in_env(p, e, env)
                    if matched_env:
                        matched = True
                        matched_envs.extend(new_envs)

                return matched, matched_envs

            def enode_matches_in_env(p: QuicheTree, e: ENode, env: Env):
                """
                :param p: QuicheTree
                :param e: ENode
                :param env: Env
                :returns: Tuple[Bool, List[Env]]
                """
                if e.key != p.value():
                    return False, [env]

                new_envs = [env]
                for arg_pattern, arg_eid in zip(p.children(), e.args):
                    matched, new_envs = match_in(arg_pattern, arg_eid, new_envs)
                    if not matched:
                        return False, [env]
                return True, new_envs

            if p.is_pattern_symbol():
                # this is a leaf variable like ?x: match it with the env
                id = p.value()
                matched = False
                matched_envs = []
                for env in envs:
                    if id not in env:
                        # create a copy of the env, keeping references to eclassids
                        env = {**env}  # expensive, but can be optimized (?)
                        env[id] = eid
                        matched = True
                        matched_envs.append(env)
                    else:
                        # check that this value matches the same thing (?)
                        if env[id] is eid:
                            matched = True
                            matched_envs.append(env)
                return matched, matched_envs
            else:
                matched = False
                matched_envs = []
                # does one of the ways to define this class match the pattern?
                for enode in eclasses[eid]:
                    for env in envs:
                        matches, new_envs = enode_matches(p, enode, [env])
                        if matches:
                            matched = True
                            matched_envs.extend(new_envs)
                return matched, matched_envs

        matches = []
        for eid in eclasses.keys():
            match, envs = match_in(pattern, eid, [{}])
            if match:
                matches.extend([(eid, env) for env in envs])
        return matches

    def _new_singleton_eclass(self):
        singleton = EClassID(self.id_counter)
        self.id_counter += 1
        return singleton

    def add_enode(self, enode: ENode):
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

    def add(self, node: QuicheTree):
        """
        Add a new node to the EGraph.

        :param node: a QuicheTree node
        :returns: the EClassID of the new ENode
        """
        return self.add_enode(
            ENode(node.value(), tuple(self.add(n) for n in node.children()))
        )

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
        e1.uses = []  # TODO: was None in original?

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

    def apply_rules(self, rules: List[Rule]):
        """
        :param rules: List[Rule]
        :returns: EGraph
        """
        canonical_eclasses = self.eclasses()

        matches = []
        for rule in rules:
            for eid, env in self.ematch(rule.lhs, canonical_eclasses):
                matches.append((rule, eid, env))
        # print(f"VERSION {self.version}")
        for rule, eid, env in matches:
            new_eid = self.subst(rule.rhs, env)
            # if eid is not new_eid:
            #     print(f"{eid} MATCHED {rule} with {env}")
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

    def subst(self, pattern: QuicheTree, env: Dict[str, EClassID]):
        """
        :param pattern: QuicheTree
        :param env: Dict[str, EClassID]
        :returns: EClassID
        """
        if pattern.is_pattern_symbol():
            return env[pattern.value()]
        else:
            enode = ENode(
                pattern.value(),
                tuple(self.subst(child, env) for child in pattern.children()),
            )
            return self.add_enode(enode)
