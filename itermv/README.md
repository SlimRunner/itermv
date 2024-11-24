# itermv
**itermv** is a command-line utility designed to simplify the renaming of multiple files in a directory. It provides flexible pattern matching using regular expressions (regex) and allows for advanced renaming options with capture groups. Additionally, `itermv` supports automatic name collision avoidance, making batch file renaming smooth and error-free.

## TODO
### Brainstorm
- current only pattern option
  - format: `[-r <file-regex>] <name-pattern>`
- replace with diverse options for renaming
  - perform a direct replacement from name individually (all, first, or last)
    - format: `--replace-each <repl-regex> <repl-string> [<file-regex>]`
    - notice the weird format of having the replacement first
    - example: use ` |_` as regex and the replacement string would override all instances of those in all names
  - provide names in pairs to be explicit what each file should be renamed to
    - format: `--rename <filename> <filename-pattern> [<filename> <filename-pattern> ...]`
    - potentially support regex on each `<file-regex>`
      - this requires exclusivity verification for all matches
    - implementation
      - aggregate source names and ignore repeats (or raise error?)
      - verify that target names are valid (collision, unique, whitelisted, etc.)
      - run the program as always, but regex for each is set to `.*`
  - provide a single pattern and a list of new names
    - format: `--rename-list <file-regex> [<name-pattern> ...]`
    - you need to decide what to do if `list of matches < list of files` or vice versa.
    - this one does not make a lot of sense. Is it worth it to code?
      - maybe not

### Idea
Leave the regex flag alone, but make it mutually exclusive with another flag that receives a list of filenames instead.

Now the name replacement can be done in one of three strategies.
- regex search
  - must read files in some order
  - regex groups are available
  - direct renaming
    - `itermv -R <filter-regex> -? <rename-pattern>`
    - algorithm
      - filter files in directory
      - generate target names
      - create tasks and validate them
      - generate schedule
      - if valid, rename
  - recurrence replacement
    - `itermv -R <filter-regex> -? <repl-regex> <repl-string>`
    - algorithm
      - filter files in directory
      - generate target names
      - create tasks and validate them
      - generate schedule
      - if valid, rename
  - list replacement
    - `itermv -R <filter-regex> -? <new-name1> <new-name2> ...`
    - items must match so this might be fragile
      - possibly allow larger lists (trim) or smaller ones (ignore)
        - make it clear when either is happening
    - algorithm
      - filter files in directory
      - generate target names
      - apply mismatch resolution
      - create tasks and validate them
      - generate schedule
      - if valid, rename
- name list
  - no regex on the list so that it is glob-friendly
  - order of provided list is preserved
  - regex groups are not available
  - direct renaming
    - only first step of algorithm changes
  - recurrence replacement
    - only first step of algorithm changes
  - list replacement
    - only first step of algorithm changes

Task validation entails:
- invalid target name on at least one OS -> error
- external collision -> error
- internal collision -> error unless allowed

### New Flags
- repl group (mutually exclusive)
  - `-? -> -p <>`, `--rename-replace`
  - `-? -> -e <>`, `--rename-each`
  - `-? -> -l <>`, `--rename-list`
- filter group (mutually exclusive)
  - `-r -> -R []`, `--regex`
  - `-r -> -L []`, `--file-list`
- filter options (inclusive)
  - `-o -> -s []`, `--sort`
  - `-i -> -r []`, `--reverse-sort`
- common group (inclusive)
  - `-s -> -i []`, `--source`
  - `-t -> -  []`, `--time-stamp-type`
  - `-T -> -  []`, `--time-separator`
  - `-n -> -  []`, `--start-number`
  - `-k -> -  []`, `--radix`
  - `-f -> -  []`, `--include-self`
  - `-x -> -  []`, `--exclude-dir`
  - `-v -> -  []`, `--verbose`
  - `-q -> -  []`, `--quiet`
  - `-o -> -O []`, `--overlap`
  - `-d -> -  []`, `--dry-run`

`<>` means required `[]` means optional

## Features
- Rename multiple files using customizable name patterns.
- Use regex capture groups to reorder or modify filenames.
- Automatic collision avoidance to prevent name conflicts (with the `-p` flag).
- Sort files based on various criteria like name, size, or modification time.
- Optional dry-run mode to preview changes before applying them.

## Requirements
No dependencies required! `itermv` is a self-contained utility that runs out of the box.

## Installation
As this utility is part of a monorepo, refer to the monorepo's [instructions for installation and setup](../README.md).

## Usage
The basic syntax of the itermv command is:
```bash
itermv [-h] [--version] [-s SOURCE] [-t {mtime,ctime,atime}] [-T CHAR] [-n NUMBER] [-k NUMBER] [-r REGEX] [-f] [-x] [-o {name,ctime,atime,mtime,size}] [-i] [-v] [-q] [-p] [-d] PATTERN
```

### Positional Argument
- `PATTERN`: The new name pattern for the files. Wrap replacement values within curly braces. Available options include:
  - `{n}`: Sequential number.
  - `{n0}`: Zero-padded sequential number.
  - `{a}`, {A}: Alphabetical counting (uppercase for `{A}`).
  - `{d}`: Date in `yyyy-mm-dd` format.
  - `{t}`: Time in `hh-mm-ss` format.
  - `{ext}`: Original file extension.
  - `{name}`: Original file name without extension.
  - `{<number>}`: Captured string from regex matching.

### Key Options
- `-r REGEX, --regex REGEX`: Filter files using a Python regular expression.
- `-p, --overlap`: Automatically resolve name collisions.
- `-v, --verbose`: List all files to be renamed.
- `-d, --dry-run`: Preview the renaming changes without applying them.
- `-s SOURCE, --source SOURCE`: Specify the source directory (defaults to the current directory).
- `-o {name,ctime,atime,mtime,size}`: Sort files by a specified criterion.

For full documentation on all the flags see the command help (`-h`).

### Example
To rename all .txt files in the current directory using regex to capture parts of the name and reformat them:

```bash
itermv -r '(\d+)-(.+)\.txt' -p '{2}-{1}.txt'
```
This will reorder filenames by swapping the digits and the text portions while ensuring no name collisions make it fail.

For a dry run to preview the changes:
```bash
itermv -r '(\d+)-(.+)\.txt' -d -p '{2}-{1}.txt'
```
