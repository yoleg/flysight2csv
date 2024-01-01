"""
A few simple output formats.

NOTE: These are not intended to be exhaustive. Use pandas dataframes for more complex output.
"""
import csv
from datetime import datetime
from itertools import chain
import json
import os
from typing import Any, Callable, Iterable, MutableMapping, TextIO

from flysight2csv.const import FLYSIGHT_CSV_DIALOG
from flysight2csv.parsed import ROW_META_FIELDS, ParsedCSV
from flysight2csv.program_params import FileFormats, ReformatParams
from flysight2csv.selection import StringSelection, filter_strings


class NothingToWriteError(Exception):
    """Raised when there are no rows to write, e.g. due to filtering."""

    pass


class FlySight2CSVDialect(csv.Dialect):
    """A CSV dialect based on FlySight 2 CSV files."""

    delimiter = ","
    doublequote = True
    lineterminator = "\r\n"
    quotechar = '"'
    quoting = csv.QUOTE_MINIMAL


csv.register_dialect(FLYSIGHT_CSV_DIALOG, FlySight2CSVDialect)


class Reformatter:
    """
    A class that can write a parsed CSV to a file descriptor in several different formats.

    NOTE: The formats are not intended to be exhaustive. Rather, the reformatted files are meant to be imported into
    other programs and libraries, such as pandas dataframes. Alternatively, use `iter_dicts` to iterate over the rows as
    dicts and write them yourself.
    """

    def __init__(
        self,
        parsed: ParsedCSV,
        params: ReformatParams,
    ):
        if not parsed.rows:
            raise ValueError(f"Parsed file has no rows! {parsed.meta.display_paths}")

        self.parsed = parsed
        self.params = params

        # derived values (cached)
        self._selected_columns: list[str] = self._select_columns()
        if not self._selected_columns:
            raise ValueError("No columns selected!")
        self._column_selection = StringSelection(include_values=self._selected_columns)

    def write_reformatted(self, fd: TextIO) -> None:
        """
        Write the reformatted file to the file descriptor.

        IMPORTANT: File handles must be opened in text mode with newline='' and encoding='utf-8'.

        * newline='' is needed to the csv library adding its own newlines. The other formats follow this convention.

        * 'utf-8' is the default Python string encoding.
        """
        if self.params.output_format == FileFormats.csv_flat:
            self.write_csv(fd, dialect=self.params.csv_dialect)
        elif self.params.output_format == FileFormats.json_lines_minimal:
            self.write_json_lines(fd, header=False, fill_nulls=False)
        elif self.params.output_format == FileFormats.json_lines_header:
            self.write_json_lines(fd, header=True, fill_nulls=False)
        elif self.params.output_format == FileFormats.json_lines_full:
            self.write_json_lines(fd, header=False, fill_nulls=True)
        else:
            raise NotImplementedError(f"Not-implemented format: {self.params.output_format}")

    def write_csv(self, target: TextIO, dialect: str = FLYSIGHT_CSV_DIALOG) -> None:
        """
        Write a flattened CSV to the file descriptor.

        IMPORTANT: If using a file handle, it must be opened in text mode with newline='' and encoding='utf-8'.

        The CSV will have a single header row with all the column names.

        :param target: The file descriptor to write to.
        :param dialect: The CSV dialect to use. Must be registered with csv.register_dialect (see Python csv library).
        """
        writer = csv.writer(target, dialect=dialect)
        header_written = False
        for row in self.parsed.iter_rows(sensors=self.params.sensors_select):
            if not header_written:
                writer.writerow(self._selected_columns)
                header_written = True
            writer.writerow(row.get_value(column_name, default=None) for column_name in self._selected_columns)
        if not header_written:
            raise NothingToWriteError("No rows selected!")

    def write_json_lines(
        self,
        target: TextIO,
        header: bool,
        fill_nulls: bool,
        default_value: Any | None = None,
        newline: str = os.linesep,
    ) -> None:
        """Write a file of JSON lines for each row."""
        if header:
            target.write(json.dumps({k: None for k in self._selected_columns}) + newline)
        for row in self.iter_dicts(add_missing=fill_nulls, default_value=default_value, converter=_converter_for_json):
            target.write(json.dumps(row) + newline)

    def iter_dicts(
        self, add_missing: bool = False, default_value: Any | None = None, converter: Callable[[Any], Any] | None = None
    ) -> Iterable[MutableMapping[str, Any]]:
        """Iterate over the rows as dicts."""
        for row in self.parsed.iter_rows(sensors=self.params.sensors_select):
            data = row.to_dict(selection=self._column_selection, converter=converter)
            if add_missing:
                for column_name in self._selected_columns:
                    data.setdefault(column_name, default_value)
            yield data

    def _select_columns(self) -> list[str]:
        parsed = self.parsed
        columns = self.params.columns_select
        sensors = self.params.sensors_select
        assert parsed.meta.columns, "No column names in file!"
        iter_data_columns = parsed.meta.iter_column_names(selection=columns, sensors=sensors)
        iter_meta_columns = filter_strings(ROW_META_FIELDS, selection=columns)
        selected_columns = list(chain(iter_meta_columns, iter_data_columns))
        if len(selected_columns) != len(set(selected_columns)):
            duplicates = sorted(x for x in selected_columns if selected_columns.count(x) > 1)
            raise Exception(f"Duplicate column names found: {duplicates}")
        return selected_columns


def _converter_for_json(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value
