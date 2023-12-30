# FlySight2CSV

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

**Source Code**: <a href="https://github.com/yoleg/flysight2csv" target="_blank">https://github.com/yoleg/flysight2csv </a>

---

Utilities for finding and reformatting FlySight 2 CSV files (SENSOR.CSV and TRACK.CSV).

:bulb: This is an early release. Please let me know how you use this tool and what features you would like to see.

## Features

The `flysight2csv` command does one or more of the following:

- Find all the FlySight 2 CSV files in one or more directories.
- Copy the files to a new directory, optionally prepending the parent directory names to the filename.
- Reformat the CSV files for easier use with other tools, such as Pandas dataframes.
  - Available formats:
    - Flat CSV (single header row)
    - JSON lines (one JSON object per line)
    - Original (unchanged)
  - Added metadata fields:
    - Original filename
    - Original line number
    - Date/time in ISO format
    - Sensor type
  - Additional options:
    - Select only the columns you need
    - Select only the sensors you need

## Possible future features

Let me know if you would like to see any of these added.

- Merge the SENSOR.CSV and TRACK.CSV files into a single CSV file.
- Trim the CSV files to just the descent or ascent portion of a flight.
- Filter the CSV files by date/time, altitude, or other criteria.
- Add units to the CSV files.
- Add a header row to the minimal JSONL file with all fields set to null.
- Show a summary of date ranges and altitudes from the discovered CSV files.
- Installers for Windows, Mac, and Linux.
- Simple graphical user interface (GUI) for selecting options and running the command.

## Installation

First, make sure you have Python 3.10 or later installed. You can check this by running:

`python --version`

If needed, you can download the latest version of Python from [python.org](https://www.python.org/downloads/).

Then, install `flysight2csv` via pip (or your favourite Python package manager):

`pip install flysight2csv`

:bulb: TIP: Consider using [pipx](https://pipxproject.github.io/pipx/) or a
[virtual environment](https://docs.python.org/3/tutorial/venv.html) to avoid installing packages globally.

Once that completes, reopen your terminal and run `flysight2csv --help` to confirm it is installed correctly.

:bulb: Additional help with `pip` is available at the [pip documentation](https://pip.pypa.io/en/stable/installation/).

## Usage

**Please note that this is an early release, and the API may change in future versions.**

By default, the command simply lists out all the CSV files it finds with a valid FlySight 2 format:

```shell
flysight2csv paths/to/files.csv /or/directories/
```

Copy the files to a new directory, prepending the date and time to the filename:

```shell
flysight2csv source/paths/ -o output/path/
```

Reformat the copied files into a "flat" CSV (single header) for use with other tools:

```shell
flysight2csv source/paths/ -o output/path/ -f csv-flat
```

For more options, see the help:

```shell
flysight2csv --help
```

## Troubleshooting

### Command not found

If the `flysight2csv` command is not available after you have installed it, make sure you have installed it in the same
Python environment you are using to run the command. For example, if you have both Python 3.12 and Python 3.10
installed, you may need to run `pip3.12 install flysight2csv` or `py -3.12 -m pip install flysight2csv` to install it
for Python 3.12.

You can also try running `python -m flysight2csv` instead of `flysight2csv`.

Finally, if you are using a virtual environment, make sure you have activated it before running the command.

## Contributors ✨

Contributions of any kind welcome! Please see the [contributing guide](CONTRIBUTING.md).

## Credits

This package was created with
[Copier](https://copier.readthedocs.io/) and the
[browniebroke/pypackage-template](https://github.com/browniebroke/pypackage-template)
project template.
