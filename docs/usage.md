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

## Supported Output Formats

When the `-o` (`--output-directory`) directory is specified, the files will be copied to that directory. The files will
be renamed to include the original directory names, and the file can be reformatted using the `--format` option.

The possible output formats (`--format` option) are:

- `unchanged` (default)
  - NOTE: this disables merging, filtering, etc... and just copies the files
- `csv-flat`
- `json-lines-minimal`
- `json-lines-header`
- `json-lines-full`

Examples of each format are available in
the [formatted test data](https://github.com/yoleg/flysight2csv/tree/main/tests/data/formatted/expected) folder.

## Command-line Parameters

TODO: describe these options in more detail

<pre>

```{include} ../tests/data/cli_expected/help.txt

```

</pre>
