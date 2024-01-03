# flysight2csv

<p align="center">
  <a href="https://github.com/yoleg/flysight2csv/actions/workflows/ci.yml?query=branch%3Amain">
    <img src="https://img.shields.io/github/actions/workflow/status/yoleg/flysight2csv/ci.yml?branch=main&label=CI&logo=github&style=flat-square" alt="CI Status" >
  </a>
  <a href="https://flysight2csv.readthedocs.io">
    <img src="https://img.shields.io/readthedocs/flysight2csv.svg?logo=read-the-docs&logoColor=fff&style=flat-square" alt="Documentation Status">
  </a>
  <a href="https://codecov.io/gh/yoleg/flysight2csv">
    <img src="https://img.shields.io/codecov/c/github/yoleg/flysight2csv.svg?logo=codecov&logoColor=fff&style=flat-square" alt="Test coverage percentage">
  </a>
</p>
<p align="center">
  <a href="https://python-poetry.org/">
    <img src="https://img.shields.io/badge/packaging-poetry-299bd7?style=flat-square&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAASCAYAAABrXO8xAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAJJSURBVHgBfZLPa1NBEMe/s7tNXoxW1KJQKaUHkXhQvHgW6UHQQ09CBS/6V3hKc/AP8CqCrUcpmop3Cx48eDB4yEECjVQrlZb80CRN8t6OM/teagVxYZi38+Yz853dJbzoMV3MM8cJUcLMSUKIE8AzQ2PieZzFxEJOHMOgMQQ+dUgSAckNXhapU/NMhDSWLs1B24A8sO1xrN4NECkcAC9ASkiIJc6k5TRiUDPhnyMMdhKc+Zx19l6SgyeW76BEONY9exVQMzKExGKwwPsCzza7KGSSWRWEQhyEaDXp6ZHEr416ygbiKYOd7TEWvvcQIeusHYMJGhTwF9y7sGnSwaWyFAiyoxzqW0PM/RjghPxF2pWReAowTEXnDh0xgcLs8l2YQmOrj3N7ByiqEoH0cARs4u78WgAVkoEDIDoOi3AkcLOHU60RIg5wC4ZuTC7FaHKQm8Hq1fQuSOBvX/sodmNJSB5geaF5CPIkUeecdMxieoRO5jz9bheL6/tXjrwCyX/UYBUcjCaWHljx1xiX6z9xEjkYAzbGVnB8pvLmyXm9ep+W8CmsSHQQY77Zx1zboxAV0w7ybMhQmfqdmmw3nEp1I0Z+FGO6M8LZdoyZnuzzBdjISicKRnpxzI9fPb+0oYXsNdyi+d3h9bm9MWYHFtPeIZfLwzmFDKy1ai3p+PDls1Llz4yyFpferxjnyjJDSEy9CaCx5m2cJPerq6Xm34eTrZt3PqxYO1XOwDYZrFlH1fWnpU38Y9HRze3lj0vOujZcXKuuXm3jP+s3KbZVra7y2EAAAAAASUVORK5CYII=" alt="Poetry">
  </a>
  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square" alt="black">
  </a>
  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=flat-square" alt="pre-commit">
  </a>
</p>
<p align="center">
  <a href="https://pypi.org/project/flysight2csv/">
    <img src="https://img.shields.io/pypi/v/flysight2csv.svg?logo=python&logoColor=fff&style=flat-square" alt="PyPI Version">
  </a>
  <img src="https://img.shields.io/pypi/pyversions/flysight2csv.svg?style=flat-square&logo=python&amp;logoColor=fff" alt="Supported Python versions">
  <img src="https://img.shields.io/pypi/l/flysight2csv.svg?style=flat-square" alt="License">
</p>

---

**Documentation**: <a href="https://flysight2csv.readthedocs.io" target="_blank">https://flysight2csv.readthedocs.io </a>

**Source Code**: <a href="https://github.com/yoleg/flysight2csv" target="_blank">https://github.com/yoleg/flysight2csv </a>

---

Utilities for finding and reformatting FlySight 2 CSV files (SENSOR.CSV and TRACK.CSV).

💡 This is an early release. Please let me know how you use this tool and what features you would like to see.

## Features

Functionality:

- Find all the FlySight 2 CSV files in one or more directories or possible file paths.
- View metadata (vars, sensors, columns, units, and first row) for each CSV file.
- Copy matching files to a single directory, prepending the parent directory names to the filename.
- Reformat the CSV files for easier use with other tools, such as Pandas dataframes.
  - Calculates ISO timestamps for non-GPS sensors from $TIME field values, if available.
  - Available formats:
    - Flat CSV (single header row)
    - JSON lines (one JSON object per line)
  - Available filters:
    - Select only the columns you need.
    - Select only the sensors you need.
- Merge the reformatted files from each directory into an additional MERGED.csv (or .jsonl) file, sorted by timestamp.

Compatibility:

- Works with Python 3.10+
- Tested on Windows, Mac, and Linux
- May be used as a Python library or command-line tool

### Possible future features

Let me know if you would like to see any of these added.

- Filter the CSV files by date/time, altitude, or other criteria.
- Show a summary of date ranges and altitudes for the discovered CSV files.
- Add units to the flattened CSV files.
- FlySight 1 output format.
- Trim the CSV files to just the descent or ascent portion of a flight.
- Installers for Windows, Mac, and Linux.
- Simple graphical user interface (GUI) for selecting options and running the command.

## Installation

The package is published on [PyPI](https://pypi.org/project/flysight2csv/) and can be installed with `pip` (or any
equivalent):

```shell
pip install flysight2csv
```

For complete installation instructions, see
the [documentation](https://flysight2csv.readthedocs.io/latest/installation.html).

## Usage

**Please note that this is an early release, and the API may change in future versions.**

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

## Troubleshooting

See the [troubleshooting](https://flysight2csv.readthedocs.io/latest/troubleshooting.html) section of the documentation.

## Contributors ✨

Contributions of any kind welcome! Please see the [contributing guide](CONTRIBUTING.md).

## Credits

This package was created with
[Copier](https://copier.readthedocs.io/) and the
[browniebroke/pypackage-template](https://github.com/browniebroke/pypackage-template)
project template.
