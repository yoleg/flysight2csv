"""Make the CLI runnable using python -m flysight2csv."""
from .cli import PROGRAM_NAME, app

app(prog_name=PROGRAM_NAME)
