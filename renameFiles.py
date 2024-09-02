import os
import re
import argparse
import datetime
import textwrap
from argparse import ArgumentParser


def main():
    args = getArguments()
    namePairs = getFileNames(args.input.path, args)

    if printVerbose(namePairs, args):
        renameFiles(namePairs)
    pass


class NewFile:
    def __init__(self, path) -> None:
        self.__path = path
        fdir, fname = os.path.split(path)
        self.__name = fname
        self.__parent = fdir

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def name(self):
        return self.__name

    @property
    def parent(self):
        return self.__parent

    @property
    def path(self):
        return self.__path


class FileEntry:
    def __init__(self, name, path) -> None:
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
    def name(self):
        return self.__name

    @property
    def extension(self):
        return self.__extension

    @property
    def parent(self):
        return self.__parent

    @property
    def path(self):
        return self.__path

    @property
    def mtime(self):
        return self.__mtime

    @property
    def atime(self):
        return self.__atime

    @property
    def size(self):
        return self.__size


class InputPath:
    def __init__(self, path) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory was not found: {path}")
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Provided file is not a directory: {path}")

        self.__path = os.path.abspath(path)

    def __repr__(self) -> str:
        return f"'{self.__path}'"

    @property
    def path(self):
        return self.__path


class NamePattern:
    def __init__(self, pattern) -> None:
        self.__pattern = pattern

    def __repr__(self) -> str:
        return f"'{self.__pattern}'"

    def evalPattern(self, **kwargs):
        return self.__pattern.format(**kwargs)


class SortingOptions:
    OPTIONS = {"name", "atime", "mtime"}
    BY_NAME = "name"
    BY_ACCESS_DATE = "atime"
    BY_MODIFY_DATE = "mtime"
    DEFAULT = BY_NAME

    def __init__(self, opt) -> None:
        if opt not in SortingOptions.OPTIONS:
            raise ValueError(f"{opt} is not a valid type")
        self.__options = {o: o == opt for o in SortingOptions.OPTIONS}
        self.__selected = opt

    def __repr__(self) -> str:
        return self.__selected

    def byName(self):
        return self.__options[SortingOptions.BY_NAME]

    def byAccessDate(self):
        return self.__options[SortingOptions.BY_ACCESS_DATE]

    def byModifyDate(self):
        return self.__options[SortingOptions.BY_MODIFY_DATE]


def positiveNumber(arg):
    value = int(arg)
    if value < 0:
        raise ValueError("Staring number must be positive")
    return value


def printVerbose(namePairs, args):
    if args.verbose:
        print("The following file names will be changed:\n")
        print(f"The common directory is: {args.input.path}")
        colSize = [0, 0]
        for f, nf in namePairs:
            colSize[0] = max(colSize[0], len(f.name))
            colSize[1] = max(colSize[1], len(nf.name))
        for f, nf in namePairs:
            print(f"    {f.name:{colSize[0]}} -> {nf.name:{colSize[1]}}")

        print()
        userInput = input("Do you want to proceed? [Y]es/[N]o: ")
        while userInput not in "YyNn":
            userInput = input("Do you want to proceed? [Y]es/[N]o: ")
        return userInput in "Yy"

    return True


def renameFiles(namePairs):
    oldNames = {oldn for oldn, newn in namePairs}

    for oldn, newn in namePairs:
        if newn in oldNames:
            raise FileExistsError("Haven't coded a name collision resolution yet")

    for oldn, newn in namePairs:
        os.rename(oldn.path, newn.path)


def getFileNames(path, options):
    files = []
    if options.filter is not None:
        files = [
            FileEntry(f, path) for f in os.listdir(path) if re.match(options.filter, f)
        ]
    else:
        files = [FileEntry(f, path) for f in os.listdir(path)]

    if not options.include_self:
        files = [f for f in files if f.path != __file__]

    if options.sort.byName():
        files = sorted(files, key=lambda file: file.name)
    if options.sort.byAccessDate():
        files = sorted(files, key=lambda file: file.atime)
    if options.sort.byModifyDate():
        files = sorted(files, key=lambda file: file.mtime)

    newFiles = []
    indexStart = options.initial_number
    padsize = len(str(indexStart + len(files)))
    for i, f in enumerate(files):
        idx = i + indexStart
        nameopts = {
            "n": idx,
            "N": f"{idx:0{padsize}d}",
            "ext": f.extension,
            "d": datetime.datetime.fromtimestamp(f.mtime),
        }
        newFile = os.path.join(path, options.pattern.evalPattern(**nameopts))
        newFiles.append((f, NewFile(newFile)))
        pass

    return newFiles


def getArguments(*args):
    parser = ArgumentParser(
        prog="fren",
        description="Provides tools to easily rename files.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs=1,
        default=os.getcwd(),
        metavar="INPUT",
        help="input directory. If ommited the current working directory will be used.",
        type=InputPath,
    )
    parser.add_argument(
        "-p",
        "--pattern",
        nargs=1,
        metavar="PATTERN",
        required=True,
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
        "--initial-number",
        nargs=1,
        default=[1],
        metavar="NUMBER",
        help="Determines the initial value.",
        type=positiveNumber,
    )
    parser.add_argument(
        "-f",
        "--filter",
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
        "-c",
        "--include-self",
        action="store_true",
        help="If present considers itself to perform renaming.",
    )
    parser.add_argument(
        "-s",
        "--sort",
        nargs=1,
        default=SortingOptions.DEFAULT,
        choices=SortingOptions.OPTIONS,
        help="Allows sorting files by some criterion.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Prompts you before renaming and lists all names to be changed.",
    )
    if len(args) > 0:
        args = parser.parse_args([a for a in args])
    else:
        args = parser.parse_args()

    args.pattern = args.pattern[0]
    args.initial_number = args.initial_number[0]
    args.filter = args.filter[0] if args.filter is not None else None
    args.sort = SortingOptions(args.sort[0])

    return args


if __name__ == "__main__":
    main()
