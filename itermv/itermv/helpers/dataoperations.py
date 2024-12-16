from itermv.components import (
    AlphaCounter,
    ArgsWrapper,
    FileEntry,
    NewFile,
    RadixCounter,
    TimeStampType,
    NamePattern,
)

import os
import re
import datetime
from typing import Any, NoReturn
from collections.abc import Callable


def askUser(args: ArgsWrapper):
    print()
    if args.quiet:
        return True
    if args.dry_run:
        print("Prompt skipped by dry-run...")
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
        print(f"The common directory is: {args.source_dir.path}\n")

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


def getTimeFormats(file: FileEntry, ttype: TimeStampType, separator: str):
    entries = {}
    sep = separator

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


def internalCollisions(ifiles: list, ofiles: list):
    return set(ifiles).intersection(set(ofiles))


def externalCollisions(ofiles: list[NewFile], innerset: set[FileEntry]):
    outSet = {}
    for file in ofiles:
        if os.path.exists(file) and file not in innerset:
            outSet.add(file.name)

    return outSet


def validateUnique(files: list, getname: Callable[[Any], str]):
    fset = set()
    for file in files:
        file = getname(file)
        if file in fset:
            return False
        fset.add(file)
    return True


def expandPatterns(
    entries: list[tuple[FileEntry, NamePattern]],
    regex: str | None,
    args: ArgsWrapper,
):
    outFiles: list[NewFile] = []
    spath = args.source_dir.path
    indexStart = args.start_number
    alpha = AlphaCounter(indexStart)
    index = RadixCounter(args.radix, indexStart)
    largestNum = RadixCounter(args.radix, indexStart + len(entries))
    padsize = len(largestNum.str())

    for file, pattern in entries:
        idx = index.str(False)
        idxUp = index.str(True)
        timeEntries = getTimeFormats(file, args.time_stamp_type, args.time_separator)
        matches = []
        rgxMatch = None

        if regex is not None:
            rgxMatch = re.search(regex, file.name)

        if rgxMatch is None:
            outFiles.append(
                NewFile(os.path.join(spath, file.name))
            )
            continue
        else:
            # get the full match and capture groups
            matches = [rgxMatch.group(0)]
            matches.extend(rgxMatch.groups())

        nameopts = {
            "n": idx,
            "N": idxUp,
            "n0": f"{idx:0>{padsize}}",
            "N0": f"{idxUp:0>{padsize}}",
            "a": alpha.str(upper=False),
            "A": alpha.str(upper=True),
            "ext": file.extension,
            "name": file.noextname,
            **timeEntries,
        }

        alpha.increase()
        index.increase()

        matches = [m if m is not None else "" for m in matches]
        fEntry = NewFile(os.path.join(spath, pattern.evalPattern(*matches, **nameopts)))
        outFiles.append(fEntry)

    return outFiles


def getFileNames(opt: ArgsWrapper):
    inFiles = opt.get_sources()

    if not opt.include_self:
        inFiles = [f for f in inFiles if f.path != __file__]

    if inFiles is None:
        opt.arg_error("fatal error: input file list is None")

    if validateUnique(inFiles, lambda f: f.name):
        opt.arg_error("fatal error: input files are guaranteed to be unique.")

    if not opt.is_source_ordered():
        if opt.sort.byName():
            inFiles = sorted(inFiles, key=lambda file: file.name, reverse=opt.reverse_sort)
        if opt.sort.byAccessDate():
            inFiles = sorted(inFiles, key=lambda file: file.atime, reverse=opt.reverse_sort)
        if opt.sort.byModifyDate():
            inFiles = sorted(inFiles, key=lambda file: file.mtime, reverse=opt.reverse_sort)
        if opt.sort.bySize():
            inFiles = sorted(inFiles, key=lambda file: file.size, reverse=opt.reverse_sort)

    destGen = opt.get_destinations()
    outFiles: list[NewFile] = []

    match opt.get_dest_type():
        case ArgsWrapper.OUT_PATTERN:
            # destGen: NamePattern
            outFiles = expandPatterns(((f, destGen) for f in inFiles), opt.regex, opt)
        case ArgsWrapper.OUT_REGEX_INLINE:
            # destGen: tuple(str, NamePattern)
            rgx, patt = destGen
            outFiles = expandPatterns(((f, patt) for f in inFiles), rgx, opt)
        case ArgsWrapper.OUT_PAIR_LIST | ArgsWrapper.OUT_FILE_LIST:
            if opt.no_plain_text:
                # destGen: list[NewFile]
                outFiles = destGen
            else:
                # destGen: list[NamePattern]
                outFiles = expandPatterns(
                    ((f, p) for f, p in zip(inFiles, destGen)), None, opt
                )

    if len(inFiles) != len(outFiles):
        opt.arg_error("Number of entries in source and destination must match.")

    validateUnique(outFiles, lambda f: f.name)
    intcoll = internalCollisions(inFiles, outFiles)
    extcoll = externalCollisions(outFiles, intcoll)
    if not opt.overlap and intcoll:
        opt.arg_error(f"Try using --overlap. There are internal collisions: {intcoll}")
    if extcoll:
        opt.arg_error(f"There are collisions with files not selected: {extcoll}")

    included: list[tuple[FileEntry, NewFile]] = []
    ignored: list[tuple[FileEntry, NewFile]] = []
    for ifile, ofile in zip(inFiles, outFiles):
        if (ifile.name.path == ofile.path):
            ignored.append(ifile, ofile)
        else:
            included.append(ifile, ofile)

    return included, ignored
