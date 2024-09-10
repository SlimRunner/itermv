from helpers import (
    getArguments,
    getFileNames,
    askUser,
    renameFiles,
    renameDisjointFiles,
    printChangesMade,
    printNameMapping,
)


def main():
    args = getArguments()
    included, ignored = getFileNames(args.source.path, args)

    printNameMapping(included, ignored, args)

    if len(included) > 0 and askUser(included, args):
        if args.overlap:
            schedule = renameFiles(included)
        else:
            schedule = renameDisjointFiles(included)

        printChangesMade(schedule, args)
    elif len(included) == 0:
        print("No changes to be made")
