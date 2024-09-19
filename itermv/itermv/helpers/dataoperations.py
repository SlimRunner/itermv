from itermv.components import (
    AlphaCounter,
    RadixCounter,
    ArgsWrapper,
    FileEntry,
    NewFile,
    InputPath,
    NamePattern,
    SortingOptions,
    BlankLinesHelpFormatter,
    TimeStampType,
    TimeSeparator,
)
from itermv.utils import nonNegativeNumber, positiveRadix
from itermv.version import __version__

import os
import re
import datetime
import textwrap
from argparse import ArgumentParser


def askUser(args: ArgsWrapper):
    print()
    if args.quiet:
        return True
    MSG = "Do you want to proceed? [Y]es/[N]o: "
    userInput = input(MSG)
    while len(userInput) != 1 or userInput not in "YyNn":
        userInput = input(MSG)
    return len(userInput) > 0 and userInput in "Yy"


def printNameMapping(
    schedule: list[tuple[FileEntry, NewFile]],
    ignored: list[tuple[FileEntry, NewFile]],
    args: ArgsWrapper,
):
    if args.dry_run:
        print("-- DRY RUN")
    if args.verbose:
        print(f"The common directory is: {args.source.path}\n")

        colSize = [0, 0]
        for o, n in schedule + ignored:
            colSize[0] = max(colSize[0], len(o.name))
            colSize[1] = max(colSize[1], len(n.name))

        if len(schedule):
            print("The following files will be changed:")
        for o, n in schedule:
            print(f"    {o.name:{colSize[0]}} -> {n.name:{colSize[1]}}")

        if len(ignored):
            print("The following files will be ignored:")
        for o, n in ignored:
            print(f"    {o.name:{colSize[0]}} -> {n.name:{colSize[1]}}")

    elif not args.quiet:
        print(f"{len(schedule)} files will be changed")
        print(f"{len(ignored)} files will be ignored")


def printChangesMade(schedule: list[tuple[str, str]], args: ArgsWrapper):
    schedule = [(os.path.basename(o), os.path.basename(n)) for o, n in schedule]
    if args.verbose:
        print("Changes performed:")
        colSize = [0, 0]
        for o, n in schedule:
            colSize[0] = max(colSize[0], len(o))
            colSize[1] = max(colSize[1], len(n))
        for o, n in schedule:
            print(f"    {o:{colSize[0]}} -> {n:{colSize[1]}}")
    elif not args.quiet:
        print(f"{len(schedule)} name changes performed")

    if args.dry_run:
        print("DRY RUN --")


def getTimeFormats(file: FileEntry, ttype: TimeStampType, separator: TimeSeparator):
    entries = {}
    sep = separator.char

    unixstamp = None
    if ttype.byAccessDate():
        unixstamp = file.atime
    if ttype.byModifyDate():
        unixstamp = file.mtime
    if ttype.byMetaDate():
        unixstamp = file.ctime

    filetime = datetime.datetime.fromtimestamp(unixstamp)
    xsec = filetime.microsecond
    filetime = filetime.replace(microsecond=0)

    entries["unixt"] = unixstamp
    entries["d"] = str(filetime.date()).replace("-", sep)
    basetime = str(filetime.time()).replace(":", sep)
    entries["t"] = basetime

    entries["tu"] = f"{basetime}{sep}{xsec:06d}"
    xsec //= 1000
    entries["tm"] = f"{basetime}{sep}{xsec:03d}"
    xsec //= 10
    entries["tc"] = f"{basetime}{sep}{xsec:02d}"

    return entries


def getFileNames(path: str, opt: ArgsWrapper):
    files = []
    includeDir = lambda f: not (opt.exclude_dir and os.path.isdir(f))
    if opt.regex is not None:
        files = [
            FileEntry(f, path)
            for f in os.listdir(path)
            if includeDir(f) and re.search(opt.regex, f)
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

    included: list[tuple[FileEntry, NewFile]] = []
    ignored: list[tuple[FileEntry, NewFile]] = []
    newFileSet = set()
    indexStart = opt.start_number
    alpha = AlphaCounter(indexStart)
    index = RadixCounter(opt.radix, indexStart)
    largestNum = RadixCounter(opt.radix, indexStart + +len(files))
    padsize = len(largestNum.str())

    for f in files:
        idx = index.str(False)
        idxUp = index.str(True)
        timeEntries = getTimeFormats(f, opt.time_type, opt.time_separator)
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
            "ext": f.extension,
            "name": f.noextname,
            **timeEntries,
        }

        alpha.increase()
        index.increase()

        matches = [m if m is not None else "" for m in matches]
        newFile = os.path.join(path, opt.pattern.evalPattern(*matches, **nameopts))
        if newFile in newFileSet:
            raise ValueError("Pattern provided does not yield unique names.")
        newFileSet.add(newFile)

        if f.path == newFile:
            ignored.append((f, NewFile(newFile)))
        else:
            included.append((f, NewFile(newFile)))

    existingFiles = {f2.path for f2 in files}
    for _, newFile in included:
        if not (opt.overlap and newFile.path in existingFiles) and os.path.exists(
            newFile.path
        ):
            if newFile.path in existingFiles:
                errMsg = "There cannot be overlap between old and new names."
            else:
                errMsg = (
                    "A name collision occurred with a file outside the selected ones."
                )
            raise FileExistsError(errMsg)

    return included, ignored


def getArguments(*args: str) -> ArgsWrapper:
    parser = ArgumentParser(
        prog="itermv",
        description="Provides tools to easily rename files within a given directory.",
        formatter_class=BlankLinesHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
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

                - {d} the date in yyyy-mm-dd format.

                - {t<c,m,u>} time in hh-mm-ss-ccmuuu format where c, m, and u
                  stand for are centi- mili- and micro-seconds respectively

                - {t} time in hh-mm-ss format.

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
        "-t",
        "--time-type",
        nargs=1,
        default=[TimeStampType.DEFAULT],
        choices=TimeStampType.OPTIONS,
        help="Specifies the type of the time stamps.",
    )
    parser.add_argument(
        "-T",
        "--time-separator",
        nargs=1,
        default=[TimeSeparator.DEFAULT],
        metavar="CHAR",
        help="Specifies the separator used for the time stamps.",
    )
    parser.add_argument(
        "-n",
        "--start-number",
        nargs=1,
        default=[0],
        metavar="NUMBER",
        help="Specifies the initial value (0 is default).",
        type=nonNegativeNumber,
    )
    parser.add_argument(
        "-k",
        "--radix",
        nargs=1,
        default=[10],
        metavar="NUMBER",
        help="Specifies the radix of the counting (10 is default).",
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
        help="If present directories are ignored.",
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
        help="If present sorting is reversed.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Lists all names to be changed.",
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
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Does not change anything. Useful in combination with verbose.",
    )

    if len(args) > 0:
        pArgs = parser.parse_args(list(args))
    else:
        pArgs = parser.parse_args()

    pArgs.source = pArgs.source[0]
    pArgs.pattern = pArgs.pattern[0]
    pArgs.time_type = TimeStampType(pArgs.time_type[0])
    pArgs.time_separator = TimeSeparator(pArgs.time_separator[0])
    pArgs.start_number = pArgs.start_number[0]
    pArgs.radix = pArgs.radix[0]
    pArgs.regex = pArgs.regex[0] if pArgs.regex is not None else None
    pArgs.sort = SortingOptions(pArgs.sort[0])

    return ArgsWrapper(pArgs)
