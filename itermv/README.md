# itermv
**itermv** is a command-line utility designed to simplify the renaming of multiple files in a directory. It provides flexible pattern matching using regular expressions (regex) and allows for advanced renaming options with capture groups. Additionally, `itermv` supports automatic name collision avoidance, making batch file renaming smooth and error-free.

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
