from typing import Dict, List

from quiche.egraph import EGraph


def verify_egraph_shape(
    actual_egraph: EGraph, expected_shape: Dict[str, Dict[str, List[str]]]
):
    eclasses = actual_egraph.eclasses()
    # assert len(eclasses) == len(expected_shape)
    for eclassid, eclass in eclasses.items():
        eclassid_str = str(eclassid)
        assert eclassid_str in expected_shape
        for enode in eclass:
            key_str = str(enode.key)
            assert key_str in expected_shape[eclassid_str]
            assert (
                tuple(str(arg) for arg in enode.args)
                in expected_shape[eclassid_str][key_str]
            )

    return True


def print_egraph(eg):
    for eid, enode in eg.eclasses().items():
        print(eid, ": ", [en.key for en in enode], " ; ", [en.args for en in enode])
