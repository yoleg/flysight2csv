(troubleshooting)=

# Troubleshooting

### Command not found

If the `flysight2csv` command is not available after you have installed it, make sure you have installed it in the same
Python environment you are using to run the command. For example, if you have both Python 3.12 and Python 3.10
installed, you may need to run `pip3.12 install flysight2csv` or `py -3.12 -m pip install flysight2csv` to install it
for Python 3.12.

You can also try running `python -m flysight2csv` instead of `flysight2csv`.

Finally, if you are using a virtual environment, make sure you have activated it before running the command.
