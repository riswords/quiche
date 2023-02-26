from typing import NamedTuple, Sequence, Tuple, Dict, List, Any, TypeVar, Generic
from abc import ABC, abstractmethod

from .quiche_tree import QuicheTree


class EClassID:
    def __init__(self, id, parent: "EClassID" = None, data: Any = None):
        self.id = id
        self.parent = parent
        self.data = data

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

    def find(self) -> "EClassID":
        if self.parent is None:
            return self
        top = self.parent.find()
        self.parent = top  # caching top
        return top


class ENode(NamedTuple):
    key: Any
    args: Tuple[EClassID, ...]

    # print it out like an s-expr
    def __repr__(self):
        if self.args:
            return f'({self.key} {" ".join(str(arg) for arg in self.args)})'
        else:
            return str(self.key)

    def canonicalize(self):
        # print("Canonize node: ", self.key, ", Canonize args: ", self.args)
        return ENode(self.key, tuple(arg.find() for arg in self.args))


D = TypeVar("D")


class EClassAnalysis(ABC, Generic[D]):
    """
    EClass Analysis, parameterized by the domain, D.

    `join` must respect semilattice laws

    1. Must maintain the invariant that:

    for every eclass in the graph,
        the analysis data for that eclass, dc, is the (lattice) LUB of the
        `make` of all nodes in that eclass

    In other words, the data in the eclass is the same as if you called
    `make` on all nodes of the eclass and then `join`ed them together

    2. `modify` is at a fixed point
    """

    def make(self, egraph: "EGraph", n: ENode) -> D:
        """
        Create a new analysis value in the domain.

        :param n: enode
        :returns: dval value in the domain
        """
        pass

    def join(self, dval1: D, dval2: D) -> D:
        """Combine two analysis values, respecting semilattice laws
        :returns: dval value in the domain
        """
        pass

    def modify(self, egraph: "EGraph", eclass: EClassID) -> EClassID:
        """(Optional) modify the eclass when its associated analysis value
        changes.
        :returns: modified eclass
        """
        pass


Subst = Dict[str, EClassID]  # type alias
EMatch = Tuple[EClassID, Subst]


class EGraph:
    def __init__(self, tree: QuicheTree = None, analysis: EClassAnalysis = None):
        self.id_counter = 0

        # quickly check whether the egraph has mutated
        self.version = 0
        self._is_saturated = False
        self.timeout = -1

        # dict<ENode_canon, EClassID_noncanon> for checking if an enode is
        # already defined
        self.hashcons: Dict[ENode, EClassID] = {}

        self._cached_eclasses: Tuple[int, Dict[EClassID, List[ENode]]] = (0, {})

        # List<EClassID> of eclasses mutated by a merge, used for `rebuild`
        self.worklist: List[EClassID] = []

        self.analysis = analysis

        self.root = None
        if tree is not None:
            self.root = self.add(tree)

    def _repr_svg_(self, show_eclass_labels: bool = True):
        from graphviz import Digraph

        def escape(x):
            escapes = [("|", "\\|"), ("<", "\\<"), (">", "\\>")]
            x = str(x)
            for old, new in escapes:
                x = x.replace(old, new)
            return x

        graph = Digraph(node_attr={"shape": "record", "height": ".1"})
        graph.attr(compound="true")
        graph.attr(ranksep="1")
        graph.attr(nodesep=".5")

        for eclass, enodes in self.eclasses().items():
            # collect all e-node edges until the sub-graph is done
            graph_edges = []
            subname = f"cluster_{eclass.id}"
            # print("SUBGRAPH NAME:", subname)
            with graph.subgraph(name=subname) as ec:
                ec.attr(style="dashed,rounded")
                if show_eclass_labels:
                    ec.attr(label=f"e{eclass.id}")
                    ec.attr(labeljust="l")
                # invisible reference node for e-nodes to point to
                ec.node(
                    f"refcluster{eclass.id}",
                    shape="point",
                    color="white",
                    height="0",
                    width="0",
                )

                for enode in enodes:
                    enode_id = str(id(enode))
                    # ec.edge(f'{eclass.id}', enode_id)

                    if hasattr(enode.key, "__name__"):
                        key = enode.key.__name__
                    else:
                        key = enode.key
                    record = [escape(key)]
                    for i, arg in enumerate(enode.args):
                        dest = f"cluster_{arg.id}"
                        # print("DRAWING EDGE TO ", dest)
                        # graph.edge(f'{enode_id}:p{i}', f'refcluster{arg.id}', lhead=dest)
                        graph_edges.append(
                            (f"{enode_id}:p{i}", f"refcluster{arg.id}", dest)
                        )
                        record.append(f"<p{i}>")
                    ec.node(enode_id, label="|".join(record))
            # We could add this in the loop above, but doing it here ensures
            # that the invisible reference nodes are consistently on the right
            for edge in graph_edges:
                graph.edge(edge[0], edge[1], lhead=edge[2])

        return graph.pipe(format="svg", encoding="utf-8")

    def write_to_svg(self, filename: str, show_eclass_labels: bool = True):
        """
        Write e-graph to file in SVG format.

        :param filename: filename to write
        :return: None
        """
        svg_xml = self._repr_svg_(show_eclass_labels=show_eclass_labels)
        with open(filename, "w") as f:
            f.write(svg_xml)

    def is_saturated(self):
        return self._is_saturated

    def ematch(
        self, pattern: QuicheTree, eclasses: Dict[EClassID, List[ENode]]
    ) -> List[EMatch]:
        """ Implementation of e-matching. Check if a pattern matches any of the
        specified e-classes.

        Args:
            pattern (QuicheTree): QuicheTree pattern to match against
            eclasses (Dict[EClassID, List[ENode]]): mapping from e-class IDs to their e-nodes

        Returns:
            List[EMatch]: a list of 2-tuples (e-class ID, substitution) indicating the e-class
            ID that matched the root of the pattern and a substitution mapping pattern symbols
            to e-class IDs. NOTE: The list of e-matches may include multiple entries with the
            same e-class ID if there are multiple matching substitutions.
        """
        def enode_matches(pattern: QuicheTree, enode: ENode, envs: List[Subst]) -> List[Subst]:
            """ Check if the pattern matches the e-node under any specified substitutions."""
            # e-node key doesn't match or e-node has wrong number of children
            if pattern.value() != enode.key or len(pattern.children()) != len(enode.args):
                return []
            # no pattern children: all envs are good
            elif not pattern.children():
                return envs
            # e-node matches and has the same number of children as the pattern
            else:
                new_envs = envs
                # for each child, check if the e-class matches the pattern,
                # threading the new set of matching substitutions through
                for pat_child, enode_child in zip(pattern.children(), enode.args):
                    new_envs = match_in_eclass(pat_child, enode_child, new_envs)
                    if not new_envs:
                        return []
                return new_envs

        def match_in_eclass(pattern: QuicheTree, eid: EClassID, envs: List[Subst]) -> List[Subst]:
            """Check if pattern matches the e-class under any specified substitutions."""
            matched_envs: List[Subst] = []
            # the root of the pattern is a symbol: in each environment, we either
            # 1. bind it to this e-class ID if the symbol isn't bound; or
            # 2. verify that the symbol was previously bound to this e-class ID
            if pattern.is_pattern_symbol():
                val = pattern.value()
                for env in envs:
                    if val not in env:
                        # (inefficiently) copy the environment because other e-classes might also match
                        new_env = {**env}
                        new_env[val] = eid
                        matched_envs.append(new_env)
                    elif env[val] is eid:
                        matched_envs.append(env)
            else:
                # Not a pattern symbol: check if any e-nodes match
                for enode in eclasses[eid.find()]:
                    matched_envs.extend(enode_matches(pattern, enode, envs))
            return matched_envs

        matches: List[EMatch] = []
        for eid in eclasses.keys():
            eclass_matches = match_in_eclass(pattern, eid, [{}])
            matches.extend([(eid, env) for env in eclass_matches])
        return matches

    def env_lookup(self, env: Subst, key: str):
        """Look up key in the env substition"""
        import ast

        # TODO: This probably shouldn't go on EGraph. Need to re-work
        for k in env.keys():
            if len(k) >= 4:
                if (
                    k[0] == "name"
                    and k[1] is ast.Name
                    and k[2] == key
                    and type(k[3]) is ast.Load
                ):
                    return env[k]
        return None

    def _new_singleton_eclass(self):
        singleton = EClassID(self.id_counter)
        self.id_counter += 1
        return singleton

    def add_enode(self, enode: ENode) -> EClassID:
        enode = enode.canonicalize()
        eclassid = self.hashcons.get(enode, None)
        if eclassid is None:
            # Node not found, so create it
            self.version += 1
            self._is_saturated = False
            eclassid = self._new_singleton_eclass()
            for arg in enode.args:
                arg.uses.append((enode, eclassid))
            self.hashcons[enode] = eclassid
            if self.analysis:
                eclassid.data = self.analysis.make(self, enode)
                self.analysis.modify(self, eclassid)
        # rhs of hashcons isn't canonicalized, so do that now
        return eclassid.find()

    def add(self, node: QuicheTree) -> EClassID:
        """
        Add a new node to the EGraph.

        :param node: a QuicheTree node
        :returns: the EClassID of the new ENode
        """
        return self.add_enode(
            ENode(node.value(), tuple(self.add(n) for n in node.children()))
        )

    def find(self, eclass_id: EClassID) -> EClassID:
        return eclass_id.find()

    def union_eclasses(self, eid1: EClassID, eid2: EClassID) -> EClassID:
        """
        Union two eclasses.

        :param eid1: EClassID
        :param eid2: EClassID
        :returns: EClassID
        """
        if eid1 is eid2:
            return eid1

        # Merge into the lower (older) eclass_id
        e1 = max(eid1, eid2)
        e2 = min(eid1, eid2)

        # Maintain invariant that uses are recorded on the parent EClassID
        e1.parent = e2
        e2.uses += e1.uses
        e1.uses = []

        return e2

    def merge(self, eclass1: EClassID, eclass2: EClassID) -> EClassID:
        e1 = eclass1.find()
        e2 = eclass2.find()
        if e1 is e2:
            return e1
        self.version += 1
        self._is_saturated = False

        new_id = self.union_eclasses(e1, e2)

        # now that eclassid e2 is worklist, nodes in the hashcons may not be
        # canonicalized, and we might discover that 2 enodes are actually the
        # same value. We use `repair` to fix this and track in the `worklist`
        # list.
        self.worklist.append(new_id)

        # Update analysis
        if self.analysis:
            data1, data2 = e1.data, e2.data
            new_id.data = self.analysis.join(data1, data2)

        return new_id

    # Ensure we have a de-duplicated version of the EGraph
    def rebuild(self):
        while self.worklist:
            # de-duplicate repeated calls to repair the same EClass
            todo = set(eid.find() for eid in self.worklist)
            self.worklist = []
            for eclassid in todo:
                self.repair(eclassid)
        self._is_saturated = True

    def repair(self, eclassid):
        """
        Repair the EClassID `eclassid` by canonicalizing all nodes in the
        uses list.
        """
        # If this happens, it probably means that `eclassid` was marked
        # for repair and then merged into another e-class. If that happens,
        # just don't worry about `eclassid` because it will be repaired
        # later (I think- unless I'm wrong, and we do need to repair...)
        if eclassid.parent is not None:
            return

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

        # Update analysis
        # Mutations that modify makes to the eclass are added to the worklist
        if self.analysis:
            self.analysis.modify(self, eclassid)
            for enode, eclass in eclassid.uses:
                new_data = self.analysis.join(
                    eclass.data, self.analysis.make(self, enode)
                )
                if new_data != eclass.data:
                    eclass.data = new_data
                    self.worklist.append(eclass)

    def search(self, searcher: "EGraphSearcher") -> Sequence[EMatch]:
        return searcher.search(self)

    def apply_rewrite(self, rewriter: "EGraphRewriter", matches: Sequence[EMatch]):
        # DOESN'T RESTORE INVARIANTS: MUST CALL REBUILD AFTERWARD
        changed = False
        for eid, env in matches:
            new_eid = rewriter.apply_to_eclass(self, eid, env)
            if eid is not new_eid:
                changed = True
            self.merge(eid, new_eid)
        return changed

    def eclasses(self):
        """
        Extract dictionary of (canonicalized) EClassIDs to ENodes
        :returns: Dict[EClassID, List[ENode]]
        """
        # Check for cached eclasses
        if self._cached_eclasses[0] == self.version:
            return self._cached_eclasses[1]

        result = {}
        for enode, eid in self.hashcons.items():
            eid = eid.find()
            if eid not in result:
                result[eid] = [enode]
            else:
                result[eid].append(enode)

        self._cached_eclasses = (self.version, result)
        return result

    def lookup_eclass(self, eclassid: EClassID):
        """
        Return all enodes associated with an EClassID.
        Warning: May be expensive, depending on egraph size. Results are cached
        but must be recomputed every time the egraph is modified.
        """
        eclassid = eclassid.find()
        result = []
        for enode, eid in self.hashcons.items():
            if eid.find() == eclassid:
                result.append(enode)
        return result


class EGraphRewriter(ABC):
    @abstractmethod
    def apply_to_eclass(self, egraph: EGraph, eid: EClassID, env: Subst) -> EClassID:
        pass


class EGraphSearcher(ABC):
    @abstractmethod
    def search(self, egraph: EGraph) -> Sequence[EMatch]:
        pass
