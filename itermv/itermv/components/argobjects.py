from itermv.components import InputPath

import argparse


# https://stackoverflow.com/a/29485128
class BlankLinesHelpFormatter(argparse.RawTextHelpFormatter):
    def _split_lines(self, text, width):
        return super()._split_lines(text, width) + [""]


class TimeStampType:
    OPTIONS = {"atime", "mtime", "ctime"}
    BY_ACCESS_DATE = "atime"
    BY_MODIFY_DATE = "mtime"
    BY_META_DATE = "ctime"
    DEFAULT = BY_ACCESS_DATE

    def __init__(self, opt: str) -> None:
        if opt not in TimeStampType.OPTIONS:
            raise ValueError(f"'{opt}' is not a valid time type")
        self.__options = {o: o == opt for o in TimeStampType.OPTIONS}
        self.__selected = opt
        print(self.__options)

    def __repr__(self) -> str:
        return self.__selected

    def byAccessDate(self) -> bool:
        return self.__options[TimeStampType.BY_ACCESS_DATE]

    def byModifyDate(self) -> bool:
        return self.__options[TimeStampType.BY_MODIFY_DATE]

    def byMetaDate(self) -> bool:
        return self.__options[TimeStampType.BY_META_DATE]


class TimeSeparator:
    DEFAULT = "-"

    def __init__(self, char: str) -> None:
        if len(char) > 1:
            raise ValueError("separator must be 1 character")

        # no need to further validate character here. The filename will
        # be validated before renaming starts
        self.__separator = char

    @property
    def char(self) -> str:
        return self.__separator


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
        self.__time_type = args.time_type
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

    @property
    def source(self) -> InputPath:
        return self.__source

    @property
    def pattern(self) -> NamePattern:
        return self.__pattern

    @property
    def time_type(self) -> TimeStampType:
        return self.__time_type

    @property
    def time_separator(self) -> TimeSeparator:
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
