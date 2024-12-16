from itermv.components import FileEntry, NewFile
from argparse import (
    Action as ArgAction,
    ArgumentParser,
    Namespace,
    RawTextHelpFormatter,
)
from typing import Any, Sequence, NoReturn
from collections.abc import Callable
import os
import re


# https://stackoverflow.com/a/29485128
class BlankLinesHelpFormatter(RawTextHelpFormatter):
    def _split_lines(self, text, width):
        return super()._split_lines(text, width) + [""]


class PairifyAction(ArgAction):
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        if len(values) % 2 != 0:
            parser.error(f"For {option_string} arguments must come in pairs.")

        out_list: list[tuple[str, str]] = []
        partial_item = None
        for i, val in enumerate(values):
            if partial_item is None:
                partial_item = val
            else:
                out_list.append((partial_item, val))
                partial_item = None

        setattr(namespace, self.dest, out_list)


class TimeStampType:
    OPTIONS = {"atime", "mtime", "ctime"}
    BY_ACCESS_DATE = "atime"
    BY_MODIFY_DATE = "mtime"
    BY_META_DATE = "ctime"
    DEFAULT = BY_MODIFY_DATE

    def __init__(self, opt: str) -> None:
        if opt not in TimeStampType.OPTIONS:
            raise ValueError(f"'{opt}' is not a valid time stamp type")
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

    def __init__(self, opt: str) -> None:
        if opt not in SortingOptions.OPTIONS:
            raise ValueError(f"'{opt}' is not a valid sorting type")
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
    IN_ALL = 0
    IN_FILE_LIST = 1
    IN_REGEX = 2
    IN_PAIR_LIST = 3
    OUT_MISSING = 10
    OUT_PATTERN = 11
    OUT_REGEX_INLINE = 12
    OUT_PAIR_LIST = 13
    OUT_FILE_LIST = 14

    def __init__(self, args) -> None:
        self.__arg_error = args.arg_error
        self.__rename_replace = args.rename_replace
        self.__rename_each = args.rename_each
        self.__rename_list = args.rename_list
        self.__rename_pairs = args.rename_pairs
        self.__regex = args.regex
        self.__file_list = args.file_list

        self.__sort = args.sort
        self.__reverse_sort = args.reverse_sort
        self.__source_dir = args.source_dir
        self.__start_number = args.start_number
        self.__dry_run = args.dry_run
        self.__overlap = args.overlap
        self.__include_self = args.include_self
        self.__exclude_dir = args.exclude_dir
        self.__verbose = args.verbose
        self.__time_stamp_type = args.time_stamp_type
        self.__time_separator = args.time_separator
        self.__radix = args.radix
        self.__no_plain_text = args.no_plain_text
        self.__quiet = args.quiet

    def is_source_ordered(self):
        return self.rename_pairs is not None or self.file_list is not None

    def get_source_type(self):
        if self.rename_pairs is not None:
            return ArgsWrapper.IN_PAIR_LIST
        elif self.regex is not None:
            return ArgsWrapper.IN_REGEX
        elif self.file_list is not None:
            return ArgsWrapper.IN_FILE_LIST
        else:
            return ArgsWrapper.IN_ALL

    def get_sources(self):
        includeDir = lambda f: not (self.exclude_dir and os.path.isdir(f))
        spath = self.source_dir

        match self.get_source_type():
            case ArgsWrapper.IN_REGEX:
                return [
                    FileEntry(f, spath)
                    for f in os.listdir(spath)
                    if includeDir(f) and re.search(self.regex, f)
                ]
            case ArgsWrapper.IN_FILE_LIST:
                return self.file_list
            case ArgsWrapper.IN_PAIR_LIST:
                return [s for s, _ in self.rename_pairs]
            case ArgsWrapper.IN_ALL:
                return [FileEntry(f, spath) for f in os.listdir(spath) if includeDir(f)]
            case _:
                return None

    def get_dest_type(self):
        if self.rename_replace is not None:
            return ArgsWrapper.OUT_PATTERN
        elif self.rename_each is not None:
            return ArgsWrapper.OUT_REGEX_INLINE
        elif self.rename_list is not None or self.rename_pairs is not None:
            if self.no_plain_text:
                return ArgsWrapper.OUT_FILE_LIST
            else:
                return ArgsWrapper.OUT_PAIR_LIST
        else:
            return ArgsWrapper.OUT_MISSING

    def get_destinations(self):
        match self.get_dest_type():
            case ArgsWrapper.OUT_PATTERN:
                return self.rename_replace
            case ArgsWrapper.OUT_REGEX_INLINE:
                return self.rename_each
            case ArgsWrapper.OUT_FILE_LIST:
                return self.rename_list
            case ArgsWrapper.OUT_PAIR_LIST:
                return [d for _, d in self.rename_pairs]
            case ArgsWrapper.OUT_MISSING:
                self.arg_error("Destination names cannot be ommited.")
            case _:
                self.arg_error("Failure in replacement exclusive group")

    @property
    def arg_error(self) -> Callable[[str], NoReturn]:
        return self.__arg_error

    @property
    def rename_replace(self) -> NamePattern:
        return self.__rename_replace

    @property
    def rename_each(self) -> tuple[str, NamePattern] | None:
        return self.__rename_each

    @property
    def rename_list(self) -> list[NewFile | NamePattern] | None:
        return self.__rename_list

    @property
    def rename_pairs(self) -> list[tuple[FileEntry, NewFile | NamePattern]] | None:
        return self.__rename_pairs

    @property
    def regex(self) -> str | None:
        return self.__regex

    @property
    def file_list(self) -> list[FileEntry] | None:
        return self.__file_list

    @property
    def sort(self) -> SortingOptions:
        return self.__sort

    @property
    def reverse_sort(self) -> bool:
        return self.__reverse_sort

    @property
    def source_dir(self) -> FileEntry:
        return self.__source_dir

    @property
    def start_number(self) -> int:
        return self.__start_number

    @property
    def dry_run(self) -> bool:
        return self.__dry_run

    @property
    def overlap(self) -> bool:
        return self.__overlap

    @property
    def include_self(self) -> bool:
        return self.__include_self

    @property
    def exclude_dir(self) -> bool:
        return self.__exclude_dir

    @property
    def verbose(self) -> bool:
        return self.__verbose

    @property
    def time_stamp_type(self) -> TimeStampType:
        return self.__time_stamp_type

    @property
    def time_separator(self) -> str:
        return self.__time_separator

    @property
    def radix(self) -> int:
        return self.__radix

    @property
    def no_plain_text(self) -> bool:
        return self.__no_plain_text

    @property
    def quiet(self) -> bool:
        return self.__quiet
