(troubleshooting)=

# Troubleshooting

### Command not found

If you are using a virtual environment, make sure you have activated it before running the command. Similarly, if you
have multiple versions of Python installed, make sure you are using the same version you installed it with.

Try running `python -m flysight2csv` instead of `flysight2csv` to get around `PATH` issues.

See also the [pip documentation](https://pip.pypa.io/en/stable/installation/).

### Unexpected exceptions or errors

Report bugs to [the flysight2csv issue page][gh-issues]. If you are reporting a bug, the following would be helpful:

- Your operating system name and version
- Output of `flysight2csv --version`
- Output when the same command is rerun with the `--tracebacks` option.
- Detailed steps to reproduce the bug.

If possible, please include a copy of the file(s) that caused the error.
