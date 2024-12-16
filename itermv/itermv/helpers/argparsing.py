from itermv.components import (
    ArgsWrapper,
    BlankLinesHelpFormatter,
    InputPath,
    NamePattern,
    SortingOptions,
    TimeStampType,
    FileEntry,
    PairifyAction,
    NewFile,
)
from itermv.utils import nonNegativeNumber, positiveRadix, isTopLevelPath
from itermv.version import __version__

import os
import textwrap
from argparse import ArgumentParser

from typing import NoReturn, TypeAlias
from collections.abc import Callable


Err_Callback: TypeAlias = Callable[[str], NoReturn]


def getInputList(path: str, flist: list[str] | None, err_cb: Err_Callback):
    if flist is None:
        return None
    name_list: list[FileEntry] = []
    name_set = set()

    for file in flist:
        if not isTopLevelPath(file):
            err_cb(f"input files must be top level")
        if file in name_set:
            err_cb(f"{file} is a duplicate destination name")
        name_set.add(file)
        try:
            name_list.append(FileEntry(file, path))
        except FileNotFoundError as err:
            err_cb(str(err))
        except Exception as err:
            raise err

    return name_list


def formatRgxRplTuple(input: list[str] | None):
    if input is None:
        return None
    if len(input) != 2:
        raise NotImplementedError("Implementation does not match expected pairs")
    
    rgx, rpl = input
    rpl = NamePattern(rpl)

    return rgx, rpl


def formatDestList(root: str, input: list[str] | None, use_plain: bool, err_cb: Err_Callback):
    if input is None:
        return None
    out_list: list[NewFile | NamePattern] = []

    if use_plain:
        name_set = set()
        for name in input:
            if not isTopLevelPath(name):
                err_cb(f"destination files must be top level")
            if name in name_set:
                err_cb(f"{name} is a duplicate destination name")
            _, name = os.path.split(name)
            name_set.add(name)
            out_list.append(NewFile(os.path.join(root, name)))
    else:
        out_list = [NamePattern(it) for it in input]

    return out_list


def formatSrcDestList(
    root: str,
    input: list[tuple[str, str]] | None,
    use_plain: bool,
    err_cb: Err_Callback,
):
    if input is None:
        return None
    out_list: list[tuple[FileEntry, NewFile | NamePattern]] = []
    if use_plain:
        src_set = set()
        dest_set = set()
        for src, dest in input:
            if not isTopLevelPath(src):
                err_cb(f"input files must be top level")
            if not isTopLevelPath(dest):
                err_cb(f"destination files must be top level")
            if src in src_set:
                err_cb(f"{src} is a duplicate source name")
            if dest in dest_set:
                err_cb(f"{dest} is a duplicate destination name")
            _, src = os.path.split(src)
            src_set.add(src)
            _, dest = os.path.split(dest)
            dest_set.add(dest)
            try:
                out_list.append(
                    (FileEntry(src, root), NewFile(os.path.join(root, dest)))
                )
            except FileNotFoundError as err:
                err_cb(str(err))
            except Exception as err:
                raise err
    else:
        src_set = set()
        for src, dest in input:
            if not isTopLevelPath(src):
                err_cb(f"input files must be top level")
            if src in src_set:
                err_cb(f"{src} is a duplicate source name")
            _, src = os.path.split(src)
            src_set.add(src)
            try:
                out_list.append((FileEntry(src, root), NamePattern(dest)))
            except FileNotFoundError as err:
                err_cb(str(err))
            except Exception as err:
                raise err

    return out_list


def getArguments(*args: str) -> ArgsWrapper:
    parser = ArgumentParser(
        prog="itermv",
        description="Provides tools to easily rename files within a given directory.",
        formatter_class=BlankLinesHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.register("type", "positive radix", positiveRadix)
    parser.register("type", "zero or greater", nonNegativeNumber)
    parser.register("type", "existing directory", InputPath)

    # DEFINE GROUPS ===========================================================

    repl_group = parser.add_argument_group(
        "replacement method",
        textwrap.dedent(
            """\
            Provides a few methods to rename files. They are mutually exclusive and choosing
            one of these options is required.
            
            The following options apply to either PATTERN or DEST unless the --plain-text
            flag is specified. Each option describes where its capture groups come from,
            and they all follow the Python string interpolation format

                - {n} or {N} a sequential number in the order specified (uppercase applies
                  when radix is greater than 10).

                - {n0} or {N0} a sequential number in the order specified padded with zeroes
                  to largest integer.

                - {n:0Kd} a sequential number in the order specified padded with zeroes to a
                  length of K characters.

                - {a} or {A} alphabetical counting.

                - {d} the date in yyyy-mm-dd format using specified separator.

                - {t} time in hh-mm-ss format using specified separator.

                - {t<c,m,u>} time in hh-mm-ss-ccmuuu format where c, m, and u stand for are
                  centi- mili- and micro-seconds respectively.

                - {ext} the extension of the original file (including the dot).

                - {name} the name of the original file without the extension.

                - {<number>} the string matched by REGEX where 0 is the entire match, and
                  any subsequent number identifies a capturing group.

                - {unixt} unix time of the last modification.
            """
        ),
    )
    repl_exc_group = repl_group.add_mutually_exclusive_group(required=True)

    slct_group = parser.add_argument_group(
        "selection method",
        textwrap.dedent(
            """\
            Provides a few methods to select files from SOURCE directory. They are mutually 
            exclusive and choosing one is optional. If ommited all files are included.
            """
        ),
    )
    slct_exc_group = slct_group.add_mutually_exclusive_group(required=False)

    sort_group = parser.add_argument_group(
        "filter sorting options",
        textwrap.dedent(
            """\
            Provides options to sort the filtered list of matches by a regex search.
            """
        ),
    )

    comm_group = parser.add_argument_group(
        "other options",
        textwrap.dedent(
            """\
            Common options to change the behavior of the operation.
            """
        ),
    )

    # DEFINE FLAGS ============================================================

    repl_exc_group.add_argument(
        "-p",
        "--rename-replace",
        nargs=1,
        metavar="PATTERN",
        help=textwrap.dedent(
            """\
            Defines a pattern that renames based on the input file name and order specified.
            If combined with --regex, the pattern can also utilize its capture groups.
            """
        ),
        type=NamePattern,
    )
    repl_exc_group.add_argument(
        "-e",
        "--rename-each",
        nargs=2,
        metavar=("REGEX", "PATTERN"),
        help=textwrap.dedent(
            """\
            Facilitates renaming a common pattern across multiple selections. Its capture
            groups come from its REGEX argument even if combined with --regex.
            """
        ),
    )
    repl_exc_group.add_argument(
        "-l",
        "--rename-list",
        nargs="+",
        metavar="DEST",
        help=textwrap.dedent(
            """\
            Must match the number of source files. Useful for column formatted rename lists.
            Recommended in combination with --file-list.
            """
        ),
    )
    repl_exc_group.add_argument(
        "-f",
        "--rename-pairs",
        nargs="+",
        metavar="SRC DEST",
        help=textwrap.dedent(
            """\
            Must have an even number of entries and define a pair of old to new name. Useful
            for column formatted rename lists or to redirect files into it.
            """
        ),
        action=PairifyAction,
    )

    slct_exc_group.add_argument(
        "-R",
        "--regex",
        nargs=1,
        metavar="REGEX",
        help="Filter pattern to select files within directory (python regex)",
    )
    slct_exc_group.add_argument(
        "-L",
        "--file-list",
        nargs="+",
        metavar="SRC",
        help=textwrap.dedent(
            """\
            Explicitly write a list of files to select in the current directory. It provides
            no capture groups.
            """
        ),
    )

    sort_group.add_argument(
        "-s",
        "--sort",
        nargs=1,
        default=SortingOptions.DEFAULT,
        choices=SortingOptions.OPTIONS,
        help="Allows sorting files by some criterion.",
    )
    sort_group.add_argument(
        "-r",
        "--reverse-sort",
        action="store_true",
        help="If present sorting is reversed.",
    )

    comm_group.add_argument(
        "-i",
        "--source-dir",
        nargs=1,
        default=os.getcwd(),
        metavar="SOURCE_DIR",
        help="source directory. If ommited the current working directory will be used.",
        type="existing directory",
    )
    comm_group.add_argument(
        "-n",
        "--start-number",
        nargs=1,
        default="0",
        metavar="NUMBER",
        help="Specifies the initial value (0 is default).",
        type="zero or greater",
    )
    comm_group.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Does not change anything. Useful in combination with verbose.",
    )
    comm_group.add_argument(
        "-O",
        "--overlap",
        action="store_true",
        help="Allow and automatically resolve collisions with existing names.",
    )
    comm_group.add_argument(
        "-F",
        "--include-self",
        action="store_true",
        help="If present regex selection considers itself.",
    )
    comm_group.add_argument(
        "-X",
        "--exclude-dir",
        action="store_true",
        help="If present regex selection ignores directories.",
    )
    comm_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Lists all names to be changed.",
    )
    comm_group.add_argument(
        "-t",
        "--time-stamp-type",
        nargs=1,
        default=TimeStampType.DEFAULT,
        choices=TimeStampType.OPTIONS,
        help="Specifies the type of the time stamps.",
    )
    comm_group.add_argument(
        "-T",
        "--time-separator",
        nargs=1,
        default="-",
        metavar="SEPARATOR",
        help="Specifies the separator used for the time stamps.",
    )
    comm_group.add_argument(
        "-k",
        "--radix",
        nargs=1,
        default="10",
        metavar="NUMBER",
        help="Specifies the radix of the counting (10 is default).",
        type="positive radix",
    )
    comm_group.add_argument(
        "-N",
        "--no-plain-text",
        action="store_true",
        help="Enables pattern replacement in DEST arguments.",
    )
    comm_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="If present all prompts are skipped.",
    )

    # WRAP NAMESPACES =========================================================

    if len(args) > 0:
        pArgs = parser.parse_args(list(args))
    else:
        pArgs = parser.parse_args()

    opt_none = lambda x: x[0] if x is not None else None
    opt_def = lambda x: x[0] if type(x) == list else x

    src_dir: InputPath = opt_def(pArgs.source_dir)
    use_plain: bool = not pArgs.no_plain_text

    setattr(pArgs, "arg_error", parser.error)
    pArgs.rename_replace = opt_none(pArgs.rename_replace)  # -> NamePattern | None
    pArgs.rename_each = formatRgxRplTuple(pArgs.rename_each)  # -> tuple[str, str] | None
    pArgs.rename_list = formatDestList(src_dir.path, pArgs.rename_list, use_plain, parser.error)
    pArgs.rename_pairs = formatSrcDestList(src_dir.path, pArgs.rename_pairs, use_plain, parser.error)
    pArgs.regex = opt_none(pArgs.regex)  # -> str | None
    pArgs.file_list = getInputList(src_dir.path, pArgs.file_list, parser.error)  # -> list[FileEntry] | None
    pArgs.sort = SortingOptions(opt_def(pArgs.sort))
    # reverse_sort # -> bool
    pArgs.source_dir = src_dir  # -> InputPath
    pArgs.start_number = opt_def(pArgs.start_number)  # -> int >= 0
    # dry_run      # -> bool
    # overlap      # -> bool
    # include_self # -> bool
    # exclude_dir  # -> bool
    # verbose      # -> bool
    pArgs.time_stamp_type = TimeStampType(opt_def(pArgs.time_stamp_type))
    pArgs.time_separator = opt_def(pArgs.time_separator)  # -> str
    pArgs.radix = opt_def(pArgs.radix)  # -> int > 0
    # no_plain_text # -> bool
    # quiet         # -> bool

    return ArgsWrapper(pArgs)
