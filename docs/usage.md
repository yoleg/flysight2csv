(usage)=

# Usage

Assuming that you've followed the {ref}`installations steps <installation>`, you're now ready to use this package.

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
