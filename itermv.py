#!/usr/bin/env python3

import os
import re
import argparse
import datetime
import textwrap
from random import randint
from argparse import ArgumentParser


def main():
    args = getArguments()
    filePairs = getFileNames(args.source.path, args)

    if askUser(filePairs, args):
        if args.overlap:
            renameFiles(filePairs)
        else:
            renameDisjointFiles(filePairs)
        print("files renamed successfully")


class NewFile:
    def __init__(self, path: str) -> None:
        self.__path = path
        fdir, fname = os.path.split(path)
        self.__name = fname
        self.__parent = fdir

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def name(self) -> str:
        return self.__name

    @property
    def parent(self) -> str:
        return self.__parent

    @property
    def path(self) -> str:
        return self.__path


class FileEntry:
    def __init__(self, name: str, path: str) -> None:
        self.__path = os.path.join(path, name)
        fullpath = self.__path
        fdir, fname = os.path.split(fullpath)
        if not os.path.exists(fullpath):
            raise FileNotFoundError(f"file does not exist: {fullpath}")
        noxname, ext = os.path.splitext(fname)
        self.__name = fname
        self.__noextname = noxname
        self.__extension = ext
        self.__parent = fdir
        self.__mtime = os.path.getmtime(fullpath)
        self.__atime = os.path.getatime(fullpath)
        # ctime is not consistent across platforms.
        self.__ctime = os.path.getctime(fullpath)
        self.__size = os.path.getsize(fullpath)

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def name(self) -> str:
        return self.__name

    @property
    def noextname(self) -> str:
        return self.__noextname

    @property
    def extension(self) -> str:
        return self.__extension

    @property
    def parent(self) -> str:
        return self.__parent

    @property
    def path(self) -> str:
        return self.__path

    @property
    def mtime(self) -> float:
        return self.__mtime

    @property
    def atime(self) -> float:
        return self.__atime

    @property
    def ctime(self) -> float:
        return self.__ctime

    @property
    def size(self) -> int:
        return self.__size


class InputPath:
    def __init__(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory was not found: {path}")
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Provided file is not a directory: {path}")

        self.__path = os.path.abspath(path)

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def path(self) -> str:
        return self.__path


class NamePattern:
    def __init__(self, pattern: str) -> None:
        self.__pattern = pattern

    def __repr__(self) -> str:
        return f"'{self.__pattern}'"

    def evalPattern(self, **kwargs) -> str:
        return self.__pattern.format(**kwargs)


class SortingOptions:
    OPTIONS = {"name", "atime", "mtime", "ctime", "size"}
    BY_NAME = "name"
    BY_ACCESS_DATE = "atime"
    BY_MODIFY_DATE = "mtime"
    BY_META_DATE = "ctime"
    BY_SIZE = "size"
    DEFAULT = BY_NAME

    def __init__(self, opt: str) -> None:
        if opt not in SortingOptions.OPTIONS:
            raise ValueError(f"'{opt}' is not a valid sort type")
        self.__options = {o: o == opt for o in SortingOptions.OPTIONS}
        self.__selected = opt

    def __repr__(self) -> str:
        return self.__selected

    def byName(self) -> bool:
        return self.__options[SortingOptions.BY_NAME]

    def byAccessDate(self) -> bool:
        return self.__options[SortingOptions.BY_ACCESS_DATE]

    def byModifyDate(self) -> bool:
        return self.__options[SortingOptions.BY_MODIFY_DATE]

    def byMetaDate(self) -> bool:
        return self.__options[SortingOptions.BY_META_DATE]

    def bySize(self) -> bool:
        return self.__options[SortingOptions.BY_SIZE]


class ArgsWrapper:
    def __init__(self, args) -> None:
        self.__source = args.source
        self.__pattern = args.pattern
        self.__start_number = args.start_number
        self.__radix = args.radix
        self.__regex = args.regex
        self.__include_self = args.include_self
        self.__exclude_dir = args.exclude_dir
        self.__sort = args.sort
        self.__reverse_sort = args.reverse_sort
        self.__verbose = args.verbose
        self.__quiet = args.quiet
        self.__overlap = args.overlap

    @property
    def source(self) -> InputPath:
        return self.__source

    @property
    def pattern(self) -> NamePattern:
        return self.__pattern

    @property
    def start_number(self) -> int:
        return self.__start_number

    @property
    def radix(self) -> int:
        return self.__radix

    @property
    def regex(self) -> str:
        return self.__regex

    @property
    def include_self(self) -> bool:
        return self.__include_self

    @property
    def exclude_dir(self) -> bool:
        return self.__exclude_dir

    @property
    def sort(self) -> SortingOptions:
        return self.__sort

    @property
    def reverse_sort(self) -> bool:
        return self.__reverse_sort

    @property
    def verbose(self) -> bool:
        return self.__verbose

    @property
    def quiet(self) -> bool:
        return self.__quiet

    @property
    def overlap(self) -> bool:
        return self.__overlap


class RadixCounter:
    def __init__(self, radix: int, start=0) -> None:
        if radix < 1:
            raise ValueError("radix cannot be negative")
        self.__radix = radix
        self.__counter = [0]
        self.setCount(start)

    def setCount(self, num: int):
        self.__counter = [num]
        while self.__counter[0] >= self.__radix:
            self.__counter.insert(0, self.__counter[0] // self.__radix)
            self.__counter[1] %= self.__radix
        if len(self.__counter) > 1 and self.__counter[0] == 0:
            self.__counter.pop(0)
        return self

    def increase(self):
        pos = len(self.__counter) - 1
        self.__counter[pos] += 1
        while self.__counter[pos] >= self.__radix:
            carry = self.__counter[pos] // self.__radix
            out = self.__counter[pos] % self.__radix
            self.__counter[pos] = out
            pos -= 1
            if pos < 0:
                if carry > 0:
                    self.__counter.insert(0, carry)
                # assuming delta is +1
                break
            else:
                self.__counter[pos] += carry
        return self

    def str(self, upper=False) -> str:
        offset = (65 if upper else 97) - 10
        if self.__radix > 36:
            raise IndexError(
                f"Not enough letters in alphabet for radix of {self.__radix}"
            )
        return "".join([chr(i + (offset if i > 9 else 48)) for i in self.__counter])

    def raw(self) -> list[int]:
        return self.__counter[:]


class AlphaCounter:
    def __init__(self, start=0) -> None:
        self.__radix = 26
        self.__counter = [0]
        self.setCount(start)

    def setCount(self, num: int):
        radix = self.__radix
        self.__counter = [num]
        while self.__counter[0] >= radix:
            self.__counter.insert(0, self.__counter[0] // radix - 1)
            self.__counter[1] %= radix
        return self

    def increase(self):
        radix = self.__radix
        pos = len(self.__counter) - 1
        self.__counter[pos] += 1
        while self.__counter[pos] >= radix:
            carry = self.__counter[pos] // radix
            out = self.__counter[pos] % radix
            self.__counter[pos] = out
            pos -= 1
            if pos < 0:
                if carry >= 0:
                    self.__counter.insert(0, carry - 1)
                break
            else:
                self.__counter[pos] += carry
        return self

    def str(self, upper=False) -> str:
        offset = 65 if upper else 97
        return "".join([chr(n + offset) for i, n in enumerate(self.__counter)])

    def raw(self) -> list[int]:
        return self.__counter[:]


def nonNegativeNumber(arg: str):
    value = int(arg)
    if value < 0:
        raise ValueError("Staring number must be positive")
    return value


def positiveRadix(arg: str):
    value = int(arg)
    if value <= 1:
        raise ValueError("Radix must be greater than 1")
    return value


def askUser(filePairs, args: ArgsWrapper):
    if args.verbose:
        print("The following file names will be changed:\n")
        print(f"The common directory is: {args.source.path}")
        colSize = [0, 0]
        for f, nf in filePairs:
            colSize[0] = max(colSize[0], len(f.name))
            colSize[1] = max(colSize[1], len(nf.name))
        for f, nf in filePairs:
            print(f"    {f.name:{colSize[0]}} -> {nf.name:{colSize[1]}}")
    else:
        print(f"{len(filePairs)} files will be changed\n")

    if args.quiet:
        return True
    print()
    MSG = "Do you want to proceed? [Y]es/[N]o: "
    userInput = input(MSG)
    while len(userInput) != 1 or userInput not in "YyNn":
        userInput = input(MSG)
    return len(userInput) > 0 and userInput in "Yy"


def isCyclic(graph: dict[str, str], visited: set[str], seed: str) -> bool:
    # this function can only handle graphs without branching
    visited.add(seed)
    node = graph[seed]
    while node is not None and node != seed:
        visited.add(node)
        if node not in graph:
            node = None
        else:
            node = graph[node]

    return node is not None


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


def renameFiles(filePairs: list[tuple[FileEntry, NewFile]]) -> None:
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

    # categorize connected components
    for node in graph:
        if node not in visited:
            if node == graph[node]:
                # ignore loops: meaning name does not change
                pass
            elif isCyclic(graph, visited, node):
                cycles.append(node)
            else:
                sequences.append(node)

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


def renameDisjointFiles(filePairs: list[tuple[FileEntry, NewFile]]) -> None:
    oldNames = {old.path for old, _ in filePairs}

    for _, new in filePairs:
        if new.path in oldNames:
            raise FileExistsError("There cannot be overlap between old and new names.")

    for old, new in filePairs:
        os.rename(old.path, new.path)


def getFileNames(path: str, opt: ArgsWrapper) -> list[tuple[FileEntry, NewFile]]:
    files = []
    includeDir = lambda f: not (opt.exclude_dir and os.path.isdir(f))
    if opt.regex is not None:
        files = [
            FileEntry(f, path)
            for f in os.listdir(path)
            if includeDir(f) and re.match(opt.regex, f)
        ]
    else:
        files = [FileEntry(f, path) for f in os.listdir(path) if includeDir(f)]

    if not opt.include_self:
        files = [f for f in files if f.path != __file__]

    if opt.sort.byName():
        files = sorted(files, key=lambda file: file.name, reverse=opt.reverse_sort)
    if opt.sort.byAccessDate():
        files = sorted(files, key=lambda file: file.atime, reverse=opt.reverse_sort)
    if opt.sort.byModifyDate():
        files = sorted(files, key=lambda file: file.mtime, reverse=opt.reverse_sort)
    if opt.sort.bySize():
        files = sorted(files, key=lambda file: file.size, reverse=opt.reverse_sort)

    newFiles = []
    newFileSet = set()
    indexStart = opt.start_number
    alpha = AlphaCounter(indexStart)
    index = RadixCounter(opt.radix, indexStart)
    largestNum = RadixCounter(opt.radix, indexStart + +len(files))
    padsize = len(largestNum.str())

    for i, f in enumerate(files):
        idx = index.str(False)
        idxUp = index.str(True)
        unixtime = f.mtime
        ftime = datetime.datetime.fromtimestamp(unixtime)
        shortdate = ftime.date()
        longtime = str(ftime.time()).replace(":", "").replace(".", "-")
        shortime = str(ftime.replace(microsecond=0).time()).replace(":", "")
        nameopts = {
            "n": idx,
            "N": idxUp,
            "n0": f"{idx:0>{padsize}}",
            "N0": f"{idxUp:0>{padsize}}",
            "a": alpha.str(),
            "A": alpha.str(upper=True),
            "d": shortdate,
            "T": longtime,
            "t": shortime,
            "ext": f.extension,
            "name": f.noextname,
            "unixt": unixtime,
        }
        alpha.increase()
        index.increase()
        newFile = os.path.join(path, opt.pattern.evalPattern(**nameopts))
        if newFile in newFileSet:
            raise ValueError("Pattern provided does not yield unique names.")
        newFileSet.add(newFile)
        newFiles.append((f, NewFile(newFile)))

    return newFiles


def getArguments(*args: str) -> ArgsWrapper:
    parser = ArgumentParser(
        prog="itermv",
        description="Provides tools to easily rename files within a given directory.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--source",
        nargs=1,
        default=[InputPath(os.getcwd())],
        metavar="SOURCE",
        help="source directory. If ommited the current working directory will be used.",
        type=InputPath,
    )
    parser.add_argument(
        "pattern",
        nargs=1,
        metavar="PATTERN",
        help=textwrap.dedent(
            """\
            Name pattern to replace current names. Wrap replacement values within
            curly braces.
                - {n} or {N} a sequential number in the order specified (uppercase
                  applies when radix is greater than 10).
                - {n0} or {N0} a sequential number in the order specified padded with
                  zeroes to largest integer
                - {n:0Kd} a sequential number in the order specified padded with
                  zeroes to a length of K characters.
                - {a} or {A} alphabetical counting.
                - {d} the date in yyyy/mm/dd format.
                - {T} time in hhmmss-uu format where u are
                  microseconds.
                - {t} time in hhmmss format.capitalize()
                - {ext} the extension of the original file
                  (including the dot).
                - {name} the name of the original file without the
                  extension.
                - {unixt} unix time of the last modification.
            """
        ),
        type=NamePattern,
    )
    parser.add_argument(
        "-n",
        "--start-number",
        nargs=1,
        default=[0],
        metavar="NUMBER",
        help="Determines the initial value.",
        type=nonNegativeNumber,
    )
    parser.add_argument(
        "-k",
        "--radix",
        nargs=1,
        default=[10],
        metavar="NUMBER",
        help="Specifies the radix of the counting.",
        type=positiveRadix,
    )
    parser.add_argument(
        "-r",
        "--regex",
        nargs=1,
        metavar="REGEX",
        help=textwrap.dedent(
            """\
            Filter pattern to include certain files (python regex). If ommited all
            files are included.
            """
        ),
    )
    parser.add_argument(
        "-f",
        "--include-self",
        action="store_true",
        help="If present considers itself to perform renaming.",
    )
    parser.add_argument(
        "-x",
        "--exclude-dir",
        action="store_true",
        help="If present only files are considered.",
    )
    parser.add_argument(
        "-o",
        "--sort",
        nargs=1,
        default=[SortingOptions.DEFAULT],
        choices=SortingOptions.OPTIONS,
        help="Allows sorting files by some criterion.",
    )
    parser.add_argument(
        "-i",
        "--reverse-sort",
        action="store_true",
        help="When present sorting is reversed.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Prompts you before renaming and lists all names to be changed.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="If present all prompts are skipped.",
    )
    parser.add_argument(
        "-p",
        "--overlap",
        action="store_true",
        help="Allow new names to overlap with existing names.",
    )
    if len(args) > 0:
        pArgs = parser.parse_args(list(args))
    else:
        pArgs = parser.parse_args()

    pArgs.source = pArgs.source[0]
    pArgs.pattern = pArgs.pattern[0]
    pArgs.start_number = pArgs.start_number[0]
    pArgs.radix = pArgs.radix[0]
    pArgs.regex = pArgs.regex[0] if pArgs.regex is not None else None
    pArgs.sort = SortingOptions(pArgs.sort[0])

    return ArgsWrapper(pArgs)


if __name__ == "__main__":
    main()
