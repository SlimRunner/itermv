from itermv.components import RadixCounter, FileEntry, NewFile
from itermv.utils import identifyCycle

import os
from sys import stderr
from random import randint


def genTempName(path: str) -> str:
    num = randint(0xFFF_FFFF_FFFF_FFFF, 0xFFFF_FFFF_FFFF_FFFF)
    alnum = RadixCounter(36, num)
    tempname = os.path.join(path, alnum.str())

    # this is a temporary solution; however, it is very unlikely to fail
    # as-is, and that is an understatement. A much more elegant solution
    # would include a thorough name generator that guarantees to find a
    # unique name in the current path.

    for _ in range(2):
        if not os.path.exists(tempname):
            return tempname
        num = randint(0xFFF_FFFF_FFFF_FFFF, 0xFFFF_FFFF_FFFF_FFFF)
        alnum = RadixCounter(36, num)
        tempname = os.path.join(path, alnum.str())

    if not os.path.exists(tempname):
        return tempname

    raise FileExistsError("Could not find an available name.")


def createValidTasklist(tasklist: list[tuple[FileEntry, NewFile]]):
    schedule: list[tuple[str, str]] = [
        (old.path, new.path) for old, new in tasklist if old.path != new.path
    ]
    sourceSet = {f for f, _ in schedule}
    targetSet = {f for _, f in schedule}
    diffset = sourceSet.intersection(targetSet)
    if len(diffset) != 0:
        errmsg = "Internal collision detected without the --overlap flag."
        errmsg += "Conflicting names are: "
        errmsg += str(diffset)
        raise FileExistsError(errmsg)

    return schedule


def createValidSchedule(tasklist: list[tuple[FileEntry, NewFile]]):
    if len(tasklist) == 0:
        return

    commonPath = tasklist[0][0].parent

    # map of renames: new -> old
    graph: dict[str, str] = {}
    visited: set[str] = set()

    # NOTE: this function assumes that neither the set of old names or
    # the set of new names contain any duplicates. The implication is
    # that the resulting graph has no branching.

    # build graph
    for fsrc, ftrg in tasklist:
        # detect branching
        if ftrg.path in graph:
            raise ValueError("Pattern provided does not yield unique names.")
        graph[ftrg.path] = fsrc.path

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

    return schedule


def renameBySchedule(schedule: list[tuple[str, str]]):
    tasklog: list[tuple[str, str]] = []
    try:
        for source, target in schedule:
            os.rename(source, target)
            tasklog.append((source, target))
    except:
        (False, tasklog)
    return (True, tasklog)


def undoSchedule(schedule: list[tuple[str, str]]):
    try:
        for source, target in reversed(schedule):
            # source and target are reversed on purpose
            os.rename(target, source)
    except Exception as ex:
        print("Fatal error: undo failed.", file=stderr)
        raise ex
