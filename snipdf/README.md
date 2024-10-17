# SniPDF
**SniPDF** is a command-line utility for extracting specific page ranges or individual pages from a PDF, allowing you to generate a new, customized PDF. Whether you need to split a large document or extract key sections, SniPDF provides a simple and flexible way to "snip" pages from your files.

## Features
- Extract individual pages or ranges of pages from a PDF.
- Combine multiple page ranges into a single output PDF.
- Lightweight and easy to use.

## Requirements
Before using SniPDF, ensure that the following dependencies are installed and system-wide accessible:
- **Ghostscript**
- **pdftk**


## Installation
As this utility is part of a monorepo, refer to the monorepo's [instructions for installation and setup](../README.md).

## Usage
The basic syntax of the SniPDF command is:
```bash
snipdf [-h] [--version] [-p RANGES [RANGES ...]] -i INPUT [-o OUTPUT]
```

### Options
- `-h, --help`: Display the help message and exit.
- `--version`: Show the program's version number and exit.
- `-p RANGES [RANGES ...], --page-ranges RANGES [RANGES ...]`: Specify the pages to extract. Each range can be:
  - A single page: `X`
  - A range of pages: `X-Y` (where `Y > X`) You can specify multiple ranges, separated by spaces.
- `-i INPUT, --input INPUT`: The input PDF file from which to extract pages.
- `-o OUTPUT, --output OUTPUT`: The filename of the output PDF. If omitted, the output will be named `untitled-?`.

### Example
To extract pages 1-3 and page 5 from `document.pdf` and save it as `output.pdf`:
```bash
snipdf -p 1-3 5 -i document.pdf -o output.pdf
```

If no output filename is provided, it will be saved with a default name like `untitled-1.pdf`:

```bash
snipdf -p 2-6 -i document.pdf
```
