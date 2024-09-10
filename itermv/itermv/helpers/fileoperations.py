from components import RadixCounter, FileEntry, NewFile
from utils import identifyCycle

import os
from random import randint


def genTempName(path: str) -> str:
    num = randint(0xFFF_FFFF_FFFF_FFFF, 0xFFFF_FFFF_FFFF_FFFF)
    alnum = RadixCounter(36, num)
    tempname = os.path.join(path, alnum.str())

    # this is a temporary solution; however, it is very unlikely to fail
    # as-is, and that is an understatement. A much more elegant solution
    # would include a thorough name generator that guarantees to finda a
    # unique name in the current path.

    for _ in range(2):
        if not os.path.exists(tempname):
            return tempname
        num = randint(0xFFF_FFFF_FFFF_FFFF, 0xFFFF_FFFF_FFFF_FFFF)
        alnum = RadixCounter(36, num)
        tempname = os.path.join(path, alnum.str())

    raise FileExistsError("Could not find an available name.")


def renameFiles(filePairs: list[tuple[FileEntry, NewFile]]) -> list[tuple[str, str]]:
    if len(filePairs) == 0:
        return

    commonPath = filePairs[0][0].parent

    # map of renames: new -> old
    graph: dict[str, str] = {}
    visited: set[str] = set()

    # NOTE: this function assumes that neither the set of old names or
    # the set of new names contain any duplicates. The implication is
    # that the resulting graph has no branching.

    # build graph
    for oldn, newn in filePairs:
        if newn.path in graph:
            # branching detected
            raise ValueError("Pattern provided does not yield unique names.")
        graph[newn.path] = oldn.path

    cycles: list[str] = []
    sequences: list[str] = []
    seqdict: dict[str, None] = {}

    # categorize connected components
    for node in graph:
        if node not in visited:
            if node == graph[node]:
                # ignore loops: meaning name does not change
                continue
            # repNode is the node which completes a cycle (None otherwise)
            # seqNode is the node that breaks a sequence (visited)
            repNode, seqNode = identifyCycle(graph, visited, node)
            if repNode is not None:
                cycles.append(node)
            else:
                if seqNode in seqdict:
                    del seqdict[seqNode]
                seqdict[node] = None

    sequences = list(seqdict.keys())

    # schedule of pairs: (old, new)
    schedule: list[tuple[str, str]] = []
    tempName: str | None = None

    # process acyclic chains
    for seq in sequences:
        node = seq
        while node in graph:
            schedule.append((graph[node], node))
            node = graph[node]
        tempName = node

    if tempName is None and len(sequences) == 0 and len(cycles) > 0:
        tempName = genTempName(commonPath)

    # process cyclic chains
    for seed in cycles:
        node = graph[seed]
        schedule.append((seed, tempName))
        schedule.append((node, seed))
        while node != seed:
            schedule.append((graph[node], node))
            node = graph[node]
        _, tail = schedule[-1]
        schedule[-1] = (tempName, tail)

    for old, new in schedule:
        os.rename(old, new)

    return schedule


def renameDisjointFiles(
    filePairs: list[tuple[FileEntry, NewFile]]
) -> list[tuple[str, str]]:
    schedule: list[tuple[str, str]] = [
        (old.path, new.path) for old, new in filePairs if old.path != new.path
    ]
    oldNames = {old for old, _ in schedule}

    for old, new in schedule:
        if new in oldNames:
            raise FileExistsError("There cannot be overlap between old and new names.")
        os.rename(old, new)

    return schedule
