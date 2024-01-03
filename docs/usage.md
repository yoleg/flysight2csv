(usage)=

# Usage

Assuming that you've followed the {ref}`installations steps <installation>`, you're now ready to use this package.

**Please note that this is an early release, and the API may change in future versions.**

Preview the files to be processed:

```shell
flysight2csv source/files/or/directories/
flysight2csv source/files/or/directories/ --info=metadata
```

Copy the files to a new directory, prepending the date and time to the filename:

```shell
flysight2csv source/files/or/directories/ -o output/path/
```

Reformat the copied files into a "flat" CSV (single header) for use with other tools:

```shell
flysight2csv source/files/or/directories/ -o output/path/ -f csv-flat
```

For more options, see the help:

```shell
flysight2csv --help
```

## Supported Formats

```{include} ../tests/data/cli_expected/formats.txt

```

## Options

TODO: describe these options in more detail

```
```{include} ../tests/data/cli_expected/help.txt

```
```
