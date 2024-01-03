(usage)=

# Usage

Assuming that you've followed the {ref}`installations steps <installation>`, you're now ready to use this package.

**Please note that this is an early release, and the API may change in future versions.**

## Examples

Preview the files to be processed:

```shell
flysight2csv source/files/or/directories/
flysight2csv source/files/or/directories/ --info=metadata
```

Copy just the TRACK.CSV files (unchanged) to a single directory, prepending the date and time to the filename:

```shell
flysight2csv source/files/or/directories/ -o output/path/ '--glob=**/TRACK.CSV'
```

Reformat all the FlySight 2 CSVs into a "flat" CSV (single header) for use with other tools:

```shell
flysight2csv source/files/or/directories/ -o output/path/ -f csv-flat
```

For more options, see the help:

```shell
flysight2csv --help
```

## Supported Output Formats

When the `-o` (`--output-directory`) directory is specified, the files will be copied to that directory. The files will
be renamed to include the original directory names, and the file can be reformatted using the `--format` option.

The possible output formats (`--format` option) are:

- `unchanged` (default)
  - NOTE: this disables merging, filtering, etc... and just copies the files
- `csv-flat` - a CSV file with a single header row
- `json-lines-minimal` - one JSON object per line, with only the fields relevant to each row
- `json-lines-header` - one JSON object per line, with a header row at the top of all the fields set to null
- `json-lines-full` - one JSON object per line, with the same fields in each object (set to null if not relevant)

Examples of each format are available in
the [formatted test data](https://github.com/yoleg/flysight2csv/tree/main/tests/data/formatted/expected) folder.

## Compatible Tools

The reformatted files can be analyzed with any tools that support CSV or JSONL file formats, such as:

- [Pandas](https://pandas.pydata.org/) (Python) - e.g. in a [Jupyter notebook](https://jupyter.org/) (author's choice)
- [csvkit](https://csvkit.readthedocs.io/) (command line)
- [jq](https://stedolan.github.io/jq/) (command line)
- [Google Sheets](https://sheets.google.com/) (web)
- [Google Looker Studio](https://lookerstudio.google.com/) (web)
- [LibreOffice Calc](https://www.libreoffice.org/discover/calc/) (Windows, macOS, Linux)
- [OpenOffice Calc](https://www.openoffice.org/product/calc.html) (Windows, macOS, Linux)
- [Numbers](https://www.apple.com/numbers/) (macOS)
- [Excel](https://www.microsoft.com/en-us/microsoft-365/excel) (Windows, macOS)

## All Command Line Options

TODO: describe these options in more detail

```{literalinclude} ../tests/data/cli_expected/help.txt
---
language: shell
---
```
