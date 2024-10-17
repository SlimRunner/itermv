import os
import re
import platform
from argparse import ArgumentParser
import subprocess as subp
import random

from snipdf.version import __version__

# TODO: add ghostscript and pdftk as dependencies instead of relying on
# the system installed libraries
GS_NAME = "gswin64c" if platform.system() == "Windows" else "gs"
PDFTK_NAME = "pdftk"


def main():
    params = Params(*perpareParams(*getParams()))
    params.buildPDF()


def findFreeName(name, ext):
    nameout = os.path.join(".", f"{name}.{ext}")
    if not os.path.exists(nameout):
        return nameout

    i = 1
    nameout = os.path.join(".", f"{name}-{i}.{ext}")
    while os.path.exists(nameout) and i <= 10:
        i += 1
        nameout = os.path.join(".", f"{name}-{i}.{ext}")

    if i <= 10:
        return nameout

    rnum = random.randrange(100_000, 1_000_000)
    nameout = os.path.join(".", f"{name}-{rnum}.{ext}")
    while i > 10 and i <= 100 and os.path.exists(nameout):
        rnum = random.randrange(100_000, 1_000_000)
        nameout = os.path.join(".", f"{name}-{rnum}.{ext}")

    if i > 100:
        raise FileTakenError("Too many attempts to find a filename.")

    return nameout


def getParams():
    parser = ArgumentParser(
        prog="snipdf",
        description="Snips ranges of pages from PDF into a single PDF",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "-p",
        "--page-ranges",
        nargs="+",
        metavar="RANGES",
        help="each range can be a single page (X) or multiple pages (X-Y) where Y > X",
    )
    parser.add_argument(
        "-i", "--input", nargs=1, metavar="INPUT", required=True, help="input file"
    )
    parser.add_argument(
        "-o",
        "--output",
        nargs=1,
        metavar="OUTPUT",
        help="filename of the output. If ommited untitled-? is used.",
    )
    args = parser.parse_args()

    return (args.input, args.output, args.page_ranges)


def expandRange(text):
    numsMatch = re.search(r"(\d+)-(\d+)", text)
    if numsMatch is None:
        num = int(text)
        return (num, num)
    numGroups = numsMatch.groups()

    if len(numGroups) != 2:
        raise ValueError(f"Range is not valid ({text})")

    return tuple([int(x) for x in (numGroups)])


def perpareParams(fin, fout, ranges):
    # fin cannot be none since it is required arg
    fin = fin[0]
    fout = findFreeName("untitled", "pdf") if fout is None else fout[0]
    # ranges cannot be none since it is required arg
    ranges = [expandRange(r) for r in ranges]
    return (fin, fout, ranges)


class FileTakenError(Exception):
    # https://stackoverflow.com/a/1319675/4938616
    def __init__(self, message, errors):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
        # Now for your custom code...
        self.errors = errors


class PageRange:
    def __init__(self, start, end):
        if start > end:
            raise ValueError(f"start ({start}) cannot be greater than end ({end})")
        self.__start = start
        self.__end = end

    def start(self):
        return self.__start

    def end(self):
        return self.__end

    def getRange(self):
        return range(self.__start, self.__end + 1)

    def __str__(self):
        return f"{self.__start}-{self.__end}"


class Params:
    def __init__(self, infile, outfile, pageRanges):
        self.__infile = infile
        self.__outfile = outfile
        self.__pranges = [PageRange(*pr) for pr in pageRanges]

    def buildPDF(self):
        GS = lambda start, end, fin, fout: [
            GS_NAME,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-dFirstPage={start}",
            f"-dLastPage={end}",
            f'-sOutputFile="{fout}"',
            fin,
        ]
        PDFTK = lambda ifiles, fout: [
            PDFTK_NAME,
            *([os.path.abspath(f) for f in ifiles]),
            "cat",
            "output",
            fout,
        ]

        if len(self.__pranges) == 1:
            print("\ncreating final pdf...")
            pages = self.__pranges[0]
            subp.check_call(
                GS(pages.start(), pages.end(), self.__infile, self.__outfile)
            )
            return

        midfiles = []

        try:
            print("\ncreating page ranges...")
            for pages in self.__pranges:
                fname = findFreeName("temp", "pdf")
                subp.check_call(GS(pages.start(), pages.end(), self.__infile, fname))
                print(f"\t{fname} file created")
                midfiles.append(fname)

            # https://stackoverflow.com/a/8159842
            print("\ncreating final pdf...")
            subp.check_call(PDFTK(midfiles, self.__outfile))
        except subp.SubprocessError as err:
            raise err
        finally:
            print("\nclearing temp files...")
            for midfile in midfiles:
                os.remove(midfile)
                print(f"\t{midfile} file deleted")

    def __str__(self):
        return f"{self.__infile}\n{self.__outfile}\n{self.__pranges}"
