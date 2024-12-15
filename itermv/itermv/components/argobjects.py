from itermv.components import InputPath, NewFile
from argparse import (
    Action as ArgAction,
    ArgumentParser,
    Namespace,
    RawTextHelpFormatter,
)
from typing import Any, Sequence, NoReturn
from collections.abc import Callable


# https://stackoverflow.com/a/29485128
class BlankLinesHelpFormatter(RawTextHelpFormatter):
    def _split_lines(self, text, width):
        return super()._split_lines(text, width) + [""]


class FilePairsAction(ArgAction):
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        if len(values) % 2 != 0:
            parser.error("For this option arguments must come in pairs.")

        out_list = []
        set_src = set()
        set_dest = set()
        for i, val in enumerate(values):
            try:
                if i % 2:
                    if val in set_src:
                        parser.error(f"{val} is a duplicate in source names")
                    set_src.add(val)
                    new_item = InputPath(val)
                else:
                    if val in set_dest:
                        parser.error(f"{val} is a duplicate in destination names")
                    set_dest.add(val)
                    new_item = NewFile(val)
            except FileNotFoundError as err:
                parser.error(str(err))
            except NotADirectoryError as err:
                parser.error(str(err))
            except SystemError as err:
                parser.error(str(err))
            except Exception as err:
                raise err
            out_list.append(new_item)

        setattr(namespace, self.dest, out_list)


class TimeStampType:
    OPTIONS = {"atime", "mtime", "ctime"}
    BY_ACCESS_DATE = "atime"
    BY_MODIFY_DATE = "mtime"
    BY_META_DATE = "ctime"
    DEFAULT = BY_ACCESS_DATE

    def __init__(self, opt: str, error_cb: Callable[[str], NoReturn]) -> None:
        if opt not in TimeStampType.OPTIONS:
            error_cb(f"'{opt}' is not a valid time type for -T/--time-stamp-type flag")
        self.__options = {o: o == opt for o in TimeStampType.OPTIONS}
        self.__selected = opt

    def __repr__(self) -> str:
        return self.__selected

    def byAccessDate(self) -> bool:
        return self.__options[TimeStampType.BY_ACCESS_DATE]

    def byModifyDate(self) -> bool:
        return self.__options[TimeStampType.BY_MODIFY_DATE]

    def byMetaDate(self) -> bool:
        return self.__options[TimeStampType.BY_META_DATE]


class NamePattern:
    def __init__(self, pattern: str) -> None:
        self.__pattern = pattern

    def __repr__(self) -> str:
        return f"'{self.__pattern}'"

    def evalPattern(self, *matches, **options) -> str:
        return self.__pattern.format(*matches, **options)


class SortingOptions:
    OPTIONS = {"name", "atime", "mtime", "ctime", "size"}
    BY_NAME = "name"
    BY_ACCESS_DATE = "atime"
    BY_MODIFY_DATE = "mtime"
    BY_META_DATE = "ctime"
    BY_SIZE = "size"
    DEFAULT = BY_NAME

    def __init__(self, opt: str, error_cb: Callable[[str], NoReturn]) -> None:
        if opt not in SortingOptions.OPTIONS:
            error_cb(f"'{opt}' is not a valid sort type for -s/--sort flag")
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
        self.__source_dir = args.source_dir
        self.__rename_replace = args.rename_replace
        self.__time_stamp_type = args.time_stamp_type
        self.__time_separator = args.time_separator
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
        self.__dry_run = args.dry_run
        self.__arg_error = args.arg_error

    @property
    def source_dir(self) -> InputPath:
        return self.__source_dir

    @property
    def rename_replace(self) -> NamePattern:
        return self.__rename_replace

    @property
    def time_stamp_type(self) -> TimeStampType:
        return self.__time_stamp_type

    @property
    def time_separator(self) -> str:
        return self.__time_separator

    @property
    def start_number(self) -> int:
        return self.__start_number

    @property
    def radix(self) -> int:
        return self.__radix

    @property
    def regex(self) -> str | None:
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

    @property
    def dry_run(self) -> bool:
        return self.__dry_run

    @property
    def arg_error(self) -> bool:
        return self.__arg_error
