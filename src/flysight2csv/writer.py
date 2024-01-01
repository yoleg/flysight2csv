"""
A few simple output formats.

NOTE: These are not intended to be exhaustive. Use pandas dataframes for more complex output.
"""
import csv
from datetime import datetime
from itertools import chain
import json
from pathlib import Path
from typing import Any, Callable, Iterable, MutableMapping, Optional, TextIO

from flysight2csv.csv import FLYSIGHT_CSV_DIALOG
from flysight2csv.parsed_csv import ROW_META_FIELDS, ParsedCSV
from flysight2csv.selection import StringSelection, filter_strings


class NothingToWriteError(Exception):
    """Raised when there are no rows to write, e.g. due to filtering."""

    pass


class Writer:
    """
    A class that can write a parsed CSV to a file descriptor in several different formats.

    NOTE: The formats are not intended to be exhaustive. Use iter_dicts with pandas dataframes for more complex output.
    """

    def __init__(
        self,
        parsed: ParsedCSV,
        columns: Optional[StringSelection] = None,  # column selection
        sensors: Optional[StringSelection] = None,  # sensor selection
    ):
        if not parsed.rows:
            raise ValueError(f"Parsed file has no rows! {parsed.meta.paths}")

        self.parsed = parsed
        self.sensor_selection = sensors

        # derived values (cached)
        self._selected_columns: list[str] = _select_columns(parsed, columns=columns, sensors=sensors)
        if not self._selected_columns:
            raise ValueError("No columns selected!")
        self._column_selection = StringSelection(include_values=self._selected_columns)

    def write_csv(self, target: TextIO | Path, dialect: str = FLYSIGHT_CSV_DIALOG) -> None:
        """
        Write a flattened CSV to the file descriptor.

        IMPORTANT: If using a file handle, it must be opened in text mode with newline='' and encoding='utf-8'.

        The CSV will have a single header row with all the column names.

        :param target: The file descriptor to write to.
        :param dialect: The CSV dialect to use. Must be registered with csv.register_dialect (see Python csv library).
        """
        if isinstance(target, Path):
            with open(target, "w", encoding="utf-8", newline="") as fd:
                return self.write_csv(fd, dialect=dialect)
        writer = csv.writer(target, dialect=dialect)
        header_written = False
        for row in self.parsed.iter_rows(sensors=self.sensor_selection):
            if not header_written:
                writer.writerow(self._selected_columns)
                header_written = True
            writer.writerow(row.get_value(column_name, default=None) for column_name in self._selected_columns)
        if not header_written:
            raise NothingToWriteError("No rows selected!")

    def write_json_lines(
        self, target: TextIO | Path, header: bool, fill_nulls: bool, default_value: Any | None = None
    ) -> None:
        """Write a file of JSON lines for each row."""
        if isinstance(target, Path):
            with open(target, "w", encoding="utf-8", newline="") as fd:
                return self.write_json_lines(fd, fill_nulls=fill_nulls, header=header, default_value=default_value)
        if header:
            target.write(json.dumps({k: None for k in self._selected_columns}) + "\n")
        for row in self.iter_dicts(add_missing=fill_nulls, default_value=default_value, converter=_converter_for_json):
            target.write(json.dumps(row) + "\n")

    def iter_dicts(
        self, add_missing: bool = False, default_value: Any | None = None, converter: Callable[[Any], Any] | None = None
    ) -> Iterable[MutableMapping[str, Any]]:
        """Iterate over the rows as dicts."""
        for row in self.parsed.iter_rows(sensors=self.sensor_selection):
            data = row.to_dict(selection=self._column_selection, converter=converter)
            if add_missing:
                for column_name in self._selected_columns:
                    data.setdefault(column_name, default_value)
            yield data


def _converter_for_json(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _select_columns(
    parsed: ParsedCSV, columns: Optional[StringSelection] = None, sensors: Optional[StringSelection] = None
) -> list[str]:
    assert parsed.meta.columns, "No column names in file!"
    iter_data_columns = parsed.meta.iter_column_names(selection=columns, sensors=sensors)
    iter_meta_columns = filter_strings(ROW_META_FIELDS, selection=columns)
    selected_columns = list(chain(iter_meta_columns, iter_data_columns))
    if len(selected_columns) != len(set(selected_columns)):
        duplicates = sorted(x for x in selected_columns if selected_columns.count(x) > 1)
        raise Exception(f"Duplicate column names found: {duplicates}")
    return selected_columns
