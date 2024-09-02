#!/usr/bin/env python3

import os
import re
import argparse
import datetime
import textwrap
from argparse import ArgumentParser


def main():
    args = getArguments()
    filePairs = getFileNames(args.source.path, args)

    if printVerbose(filePairs, args):
        print("dummy: names changed")
        # renameFiles(filePairs)
    pass


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
        _, ext = os.path.splitext(fullpath)
        self.__name = fname
        self.__extension = ext
        self.__parent = fdir
        self.__mtime = os.path.getmtime(fullpath)
        self.__atime = os.path.getatime(fullpath)
        self.__size = os.path.getsize(fullpath)
        # getting the creation time is problematic and its most of the
        # time similar to modification time. With this trade off in mind
        # I have decided to not compute it.

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def name(self) -> str:
        return self.__name

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
    OPTIONS = {"name", "atime", "mtime", "size"}
    BY_NAME = "name"
    BY_ACCESS_DATE = "atime"
    BY_MODIFY_DATE = "mtime"
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

    def bySize(self) -> bool:
        return self.__options[SortingOptions.BY_SIZE]


class ArgsWrapper:
    def __init__(self, args) -> None:
        self.__source = args.source
        self.__pattern = args.pattern
        self.__start_number = args.start_number
        self.__regex = args.regex
        self.__include_self = args.include_self
        self.__exclude_dir = args.exclude_dir
        self.__sort = args.sort
        self.__reverse_sort = args.reverse_sort
        self.__verbose = args.verbose
        self.__quiet = args.quiet

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


def positiveNumber(arg: str):
    value = int(arg)
    if value < 0:
        raise ValueError("Staring number must be positive")
    return value


def printVerbose(filePairs, args: ArgsWrapper):
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
    while len(userInput) > 1 or userInput not in "YyNn":
        userInput = input(MSG)
    return userInput in "Yy"


def renameFiles(filePairs: list[tuple[FileEntry, NewFile]]) -> None:
    oldNames = {oldn for oldn, newn in filePairs}

    for oldn, newn in filePairs:
        if newn in oldNames:
            raise FileExistsError("Haven't coded a name collision resolution yet")

    for oldn, newn in filePairs:
        os.rename(oldn.path, newn.path)


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
    padsize = len(str(indexStart + len(files)))
    for i, f in enumerate(files):
        idx = i + indexStart
        unixtime = f.mtime
        ftime = datetime.datetime.fromtimestamp(unixtime)
        shortdate = ftime.date()
        longtime = str(ftime.time()).replace(":", "").replace(".", "-")
        shortime = str(ftime.replace(microsecond=0).time()).replace(":", "")
        nameopts = {
            "n": idx,
            "N": f"{idx:0{padsize}d}",
            "ext": f.extension,
            "UT": unixtime,
            "d": shortdate,
            "T": longtime,
            "t": shortime,
        }
        newFile = os.path.join(path, opt.pattern.evalPattern(**nameopts))
        if newFile in newFileSet:
            raise ValueError("Pattern provided does not yield unique names.")
        newFileSet.add(newFile)
        newFiles.append((f, NewFile(newFile)))
        pass

    return newFiles


def getArguments(*args: str) -> ArgsWrapper:
    parser = ArgumentParser(
        prog="itermv",
        description="Provides tools to easily rename files.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--source",
        nargs=1,
        default=[InputPath(os.getcwd())],
        metavar="INPUT",
        help="input directory. If ommited the current working directory will be used.",
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
                - {n} is replaced by a sequential number in the order specified.
                - {N} is replaced by a sequential number in the order specified
                  padded to the largest integer.
                - {ext} is replaced by the extension of the original file.
                - {d} is replaced by a date in yyyy/mm/dd format.
            """
        ),
        type=NamePattern,
    )
    parser.add_argument(
        "-n",
        "--start-number",
        nargs=1,
        default=[1],
        metavar="NUMBER",
        help="Determines the initial value.",
        type=positiveNumber,
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
        "-k",
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
    if len(args) > 0:
        pArgs = parser.parse_args([a for a in args])
    else:
        pArgs = parser.parse_args()

    pArgs.source = pArgs.source[0]
    pArgs.pattern = pArgs.pattern[0]
    pArgs.start_number = pArgs.start_number[0]
    pArgs.regex = pArgs.regex[0] if pArgs.regex is not None else None
    pArgs.sort = SortingOptions(pArgs.sort[0])

    return ArgsWrapper(pArgs)


if __name__ == "__main__":
    main()