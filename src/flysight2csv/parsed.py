"""Data classes for parsed FlySight 2 CSV files."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
import itertools
from pathlib import PurePath
from typing import Any, Callable, Iterable, MutableMapping

from flysight2csv.selection import StringSelection, filter_strings

DictFactory = Callable[[], MutableMapping[str, Any]]


@dataclass
class DataRowMeta:
    """A single row of data from a FlySight 2 CSV file."""

    timestamp: datetime
    sensor_name: str  # e.g. 'GNSS' or 'IMU'
    file_path: str
    line_number: int
    offset_timestamp: datetime | None = None  # what was added to the time in seconds value to get the timestamp
    valid_offset: bool = False  # this row's timestamp was calculated using a valid GPS offset

    @property
    def location(self) -> str:
        """The human-readable location of this row, e.g. '23-10-08/15-26-01/TRACK.CSV:123'."""
        return f"{self.file_path}:{self.line_number}"

    @property
    def safe_timestamp_sort_key(self) -> tuple[datetime, int]:
        """Return a tuple that can be used to sort data rows by timestamp, falling back to line number."""
        return self.timestamp, self.line_number

    def to_dict(
        self,
        selection: StringSelection | None = None,
        prefix: str = "",
        factory: DictFactory = dict,
        converter: Callable[[Any], Any] | None = None,
    ) -> MutableMapping[str, Any]:
        """Return a dictionary representation of this metadata."""
        result = factory()
        for string in filter_strings(ROW_META_FIELDS, selection):
            value = getattr(self, string)
            if converter is not None:
                value = converter(value)
            result[f"{prefix}{string}"] = value
        return result


ROW_META_FIELDS = {f.name: f for f in dataclasses.fields(DataRowMeta)}


@dataclass
class DataRow:
    """A single row of data from a FlySight 2 CSV file."""

    meta: DataRowMeta
    values: dict[str, Any]

    def to_dict(
        self,
        selection: StringSelection | None = None,  # applies before prefixes
        metadata_only: bool = False,
        meta_prefix: str = "",
        values_prefix: str = "",
        factory: DictFactory = dict,
        converter: Callable[[Any], Any] | None = None,
    ) -> MutableMapping[str, Any]:
        """Return a dictionary representation of this row."""
        result = self.meta.to_dict(prefix=meta_prefix, selection=selection, factory=factory, converter=converter)
        if metadata_only:
            return result
        for column_name in filter_strings(self.values, selection=selection):
            key = f"{values_prefix}{column_name}"
            if result.get(key):
                raise ValueError(f"Value key {key} overlaps with a metadata key! Please set a different prefix.")
            value = self.values[column_name]
            if converter is not None:
                value = converter(value)
            result[key] = value
        return result

    def get_value(self, column_name: str, default: Any = None) -> Any:
        """Return the value for the given column name."""
        if column_name in ROW_META_FIELDS:
            return getattr(self.meta, column_name)
        return self.values.get(column_name, default)


@dataclass(repr=False)
class CSVMeta:
    """The metadata of a FlySight 2 CSV file."""

    # metadata from parser
    paths: list[PurePath] = field(default_factory=list)  # optional, for debug/ info
    display_paths: list[str] = field(default_factory=list)  # optional, for debug/ info

    # metadata from FlySight 2 Header
    vars: dict[str, str] = field(default_factory=dict)
    columns: dict[str, list[str]] = field(default_factory=dict)  # row type -> column names
    units: dict[str, dict[str, str]] = field(default_factory=dict)  # row type -> column name -> unit
    is_flysight2_file: bool = False  # true if the first line indicates this is a FlySight 2 CSV file
    complete_header: bool = False  # true if the FlySight 2 header section is complete (i.e. $DATA row was found)

    def iter_column_names(
        self,
        selection: StringSelection | None = None,
        sensors: StringSelection | None = None,
    ) -> Iterable[str]:
        """
        Iterate over all the column names found in this CSV.

        :param selection: If specified, only return column names that match the selection.
        :param sensors: If specified, only return column names for the sensors matching the selection.
        """
        yielded = set()
        for sensor, columns in self.columns.items():
            if sensors and not sensors.matches(sensor):
                continue
            for column in columns:
                if column in yielded:
                    continue
                if selection and not selection.matches(column):
                    continue
                yielded.add(column)
                yield column

    def __repr__(self) -> str:
        """Simple repr for debugging."""
        parameter_strings = []
        for key, value in vars(self).items():
            value = f"({len(value)})" if key == "paths" and value else repr(value)
            parameter_strings.append(f"{key}={value}")
        parameters = ", ".join(parameter_strings)
        return f"{self.__class__.__name__}({parameters})"

    def merge_with(self, other: CSVMeta, allow_vars_mismatch: bool = False) -> CSVMeta:
        """Return a new CSVMeta that combines this one with another."""
        if not isinstance(other, CSVMeta):
            raise TypeError(f"Cannot merge with {type(other).__name__}.")
        if not allow_vars_mismatch and self.vars and self.vars != other.vars:
            raise ValueError(f"VAR metadata mismatch! {self.vars} != {other.vars}")
        return CSVMeta(
            paths=self.paths + other.paths,
            display_paths=self.display_paths + other.display_paths,
            vars=self.vars | other.vars,
            columns=self.columns | other.columns,
            units=self.units | other.units,
            complete_header=self.complete_header and other.complete_header,
        )

    def __add__(self, other: CSVMeta) -> CSVMeta:
        """Combine with another parsed CSV."""
        return self.merge_with(other)


@dataclass(repr=False)
class ParsedCSV:
    """A parsed FlySight 2 CSV file."""

    meta: CSVMeta = field(default_factory=CSVMeta)
    rows: list[DataRow] = field(default_factory=list)
    could_not_fix_time: bool = False  # true if $TIME data was unavailable to calculate timestamps for non-GPS data
    format_errors: list[str] = field(default_factory=list)

    def iter_warnings(self) -> Iterable[str]:
        """Iterate over potential problems that affect even validly-formatted files."""
        if self.could_not_fix_time:
            yield "No $TIME columns available. Could not fix timestamps for non-GPS data."

    def __repr__(self) -> str:
        """Simple repr for debugging."""
        parameter_strings = []
        for key, value in vars(self).items():
            value = f"({len(value)})" if key == "rows" and value else repr(value)
            parameter_strings.append(f"{key}={value}")
        parameters = ", ".join(parameter_strings)
        return f"{self.__class__.__name__}({parameters})"

    def iter_rows(self, sensors: StringSelection | None = None) -> Iterable[DataRow]:
        """Iterate over data rows for the given types."""
        return (row for row in self.rows if sensors is None or sensors.matches(row.meta.sensor_name))

    def merge_with(
        self, other: ParsedCSV, sort_by_timestamp: bool = False, allow_vars_mismatch: bool = False
    ) -> ParsedCSV:
        """Return a new ParsedCSV that combines this one with another."""
        if not isinstance(other, ParsedCSV):
            raise TypeError(f"Cannot merge with {type(other).__name__}.")
        if sort_by_timestamp:
            merged_rows = sorted(itertools.chain(self.rows, other.rows), key=lambda x: x.meta.safe_timestamp_sort_key)
        else:
            merged_rows = self.rows + other.rows
        return ParsedCSV(
            meta=self.meta.merge_with(other.meta, allow_vars_mismatch=allow_vars_mismatch),
            rows=merged_rows,
            could_not_fix_time=self.could_not_fix_time or other.could_not_fix_time,
            format_errors=self.format_errors + other.format_errors,
        )

    def __add__(self, other: ParsedCSV) -> ParsedCSV:
        """Combine with another parsed CSV."""
        return self.merge_with(other)

    def sort_by_timestamp(self) -> None:
        """Sort data rows in place by timestamp ."""
        self.rows = sorted(self.rows, key=lambda x: x.meta.safe_timestamp_sort_key)
