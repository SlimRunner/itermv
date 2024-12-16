from itermv.helpers import (
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
    included, ignored = getFileNames(args)

    printNameMapping(included, ignored, args)

    if len(included) > 0 and askUser(args):
        if args.overlap:
            schedule = renameFiles(included, args.dry_run)
        else:
            schedule = renameDisjointFiles(included, args.dry_run)

        printChangesMade(schedule, args)
    elif len(included) == 0:
        print("\nNo files are selected.")
