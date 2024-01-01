import csv

FLYSIGHT_CSV_DIALOG = "flysight2csv"


class FlySight2CSVDialect(csv.Dialect):
    """A CSV dialect based on actual FlySight CSV files."""

    delimiter = ","
    doublequote = True
    lineterminator = "\r\n"
    quotechar = '"'
    quoting = csv.QUOTE_MINIMAL


csv.register_dialect(FLYSIGHT_CSV_DIALOG, FlySight2CSVDialect)
