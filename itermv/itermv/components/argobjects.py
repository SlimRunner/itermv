from components import InputPath

import re

class NamePattern:
    def __init__(self, pattern: str) -> None:
        self.__pattern = pattern

    def __repr__(self) -> str:
        return f"'{self.__pattern}'"

    def evalPattern(self, *matches, **kwargs) -> str:
        return self.__pattern.format(*matches, **kwargs)


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
