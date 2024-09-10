from components import (
    AlphaCounter,
    RadixCounter,
    ArgsWrapper,
    FileEntry,
    NewFile,
    InputPath,
    NamePattern,
    SortingOptions,
)
from utils import identifyCycle, nonNegativeNumber, positiveRadix

import os
import re
import datetime
import textwrap
import argparse
from argparse import ArgumentParser


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
    elif not args.quiet:
        print(f"{len(filePairs)} files will be changed")

    if args.quiet:
        return True
    print()
    MSG = "Do you want to proceed? [Y]es/[N]o: "
    userInput = input(MSG)
    while len(userInput) != 1 or userInput not in "YyNn":
        userInput = input(MSG)
    return len(userInput) > 0 and userInput in "Yy"


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

    newFiles: list[tuple[FileEntry, NewFile]] = []
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
        matches = []
        if opt.regex is not None:
            rawMatches = re.search(opt.regex, f.name)
            matches = [rawMatches.group(0)]
            matches.extend(rawMatches.groups())
        nameopts = {
            "n": idx,
            "N": idxUp,
            "n0": f"{idx:0>{padsize}}",
            "N0": f"{idxUp:0>{padsize}}",
            "a": alpha.str(upper=False),
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
        newFile = os.path.join(path, opt.pattern.evalPattern(*matches, **nameopts))
        if newFile in newFileSet:
            raise ValueError("Pattern provided does not yield unique names.")
        newFileSet.add(newFile)
        newFiles.append((f, NewFile(newFile)))

    existingFiles = {f2.path for f2 in files}
    for _, file in newFiles:
        if not (opt.overlap and file.path in existingFiles) and os.path.exists(
            file.path
        ):
            if file.path in existingFiles:
                errMsg = "There cannot be overlap between old and new names."
            else:
                errMsg = (
                    "A name collision occurred with a file outside the selected ones."
                )
            raise FileExistsError(errMsg)

    return newFiles


# https://stackoverflow.com/a/29485128
class BlankLinesHelpFormatter(argparse.RawTextHelpFormatter):
    def _split_lines(self, text, width):
        return super()._split_lines(text, width) + [""]


def getArguments(*args: str) -> ArgsWrapper:
    parser = ArgumentParser(
        prog="itermv",
        description="Provides tools to easily rename files within a given directory.",
        formatter_class=BlankLinesHelpFormatter,
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

                - {n0} or {N0} a sequential number in the order specified padded
                  with zeroes to largest integer

                - {n:0Kd} a sequential number in the order specified padded with
                  zeroes to a length of K characters.

                - {a} or {A} alphabetical counting.

                - {d} the date in yyyy/mm/dd format.

                - {T} time in hhmmss-uu format where u are microseconds.

                - {t} time in hhmmss format.capitalize()

                - {ext} the extension of the original file (including the dot).

                - {name} the name of the original file without the extension.

                - {<number>} the string matched by REGEX where 0 is the entire
                  match, and any subsequent number identifies a capturing group.

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
