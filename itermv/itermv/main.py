from helpers import (
    getArguments,
    getFileNames,
    askUser,
    renameFiles,
    renameDisjointFiles,
)


def main():
    args = getArguments()
    filePairs = getFileNames(args.source.path, args)

    renameCount = 0
    if askUser(filePairs, args):
        if args.overlap:
            renameCount = renameFiles(filePairs)
        else:
            renameCount = renameDisjointFiles(filePairs)
        if args.verbose:
            print(f"{renameCount} renames performed")
