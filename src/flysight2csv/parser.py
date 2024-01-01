"""Parser for FlySight 2 CSV file format."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path, PurePath
import re
from typing import Any, Iterable

from flysight2csv.parsed import CSVMeta, DataRow, DataRowMeta, ParsedCSV
from flysight2csv.program_params import ParserOptions

logger = logging.getLogger(__name__)

TIME_COL = "time"


class UnexpectedFormatError(Exception):
    """Raised when the input file is not in the expected format and strict mode is enabled."""


@dataclass
class ParserState:
    """Parser state that changes during the parsing but is not returned with the result."""

    current_offset_datetime: datetime | None = None
    current_line_number: int = 0
    warned_messages: set[str] = field(default_factory=set)
    ignored_messages: list[str] = field(default_factory=list)


class Parser:
    """Parser for a single FlySight 2 CSV file."""

    GPS_START_DATE = datetime(1980, 1, 6, 0, 0, 0)
    EXPECTED_HEADER = "$FLYS,1"
    LINE_TYPE_PATTERN = re.compile(r"^\$[A-Z]+$")
    ROW_COL = "$COL"
    ROW_DATA = "$DATA"
    ROW_UNIT = "$UNIT"
    ROW_VAR = "$VAR"
    ROW_TIME = "$TIME"

    def __init__(self, path: str | PurePath, options: ParserOptions):
        """Initialize a FlySight2CSVParser."""
        self.options = options
        self.display_path = self.options.format_display_path(path)
        meta = CSVMeta(
            paths=[path] if isinstance(path, PurePath) else [],
            display_paths=[self.display_path],
        )
        self.parsed = ParsedCSV(meta=meta)
        self.state = ParserState()

    @property
    def offset_datetime(self) -> datetime | None:
        """The datetime added to the timestamp of non-GPS data."""
        return self.options.offset_datetime or self.state.current_offset_datetime

    @offset_datetime.setter
    def offset_datetime(self, value: datetime) -> None:
        self._error_if(value.tzinfo, f"unexpected timezone: {value.tzinfo}")
        if self.parsed.could_not_fix_time:
            # recalculate the timestamps for all previous rows, now that we have a valid offset
            for row in self.parsed.rows:
                row.meta.timestamp = value + timedelta(seconds=row.values[TIME_COL])
                row.meta.offset_timestamp = value
                row.meta.valid_offset = True
            self.parsed.could_not_fix_time = False
        self.state.current_offset_datetime = value

    def _error_if(self, condition: Any, message: str) -> bool:
        """
        Record a format error if the condition is True.

        If strict mode is enabled, raise an UnexpectedFormatError instead.

        :param condition: a condition to check for truthiness
        :param message: the message to log/ raise
        :return: True if the condition is True, False otherwise
        """
        if not condition:
            return False
        if message in self.state.warned_messages:  # avoid duplicate warnings
            return True
        self.state.warned_messages.add(message)
        if self.options.ignore_all_format_errors:
            self.state.ignored_messages.append(message)
            return True
        if self.options.ignored_format_errors and self.options.ignored_format_errors.matches(message):
            self.state.ignored_messages.append(message)
            return True
        line_number = self.state.current_line_number
        location = self.display_path if line_number is None else f"{self.display_path}:{line_number}"
        formatted_message = f"{location}: {message}"
        self.parsed.format_errors.append(formatted_message)
        if not self.options.continue_on_format_error:
            raise UnexpectedFormatError(formatted_message)
        logger.error(f"Unexpected format: {formatted_message}")
        return True

    def parse(self, line_iterator: Iterable[str]) -> ParsedCSV:
        """Parse the CSV file lines."""
        self._error_if(self.parsed.meta.vars, "Reusing parser may result in unexpected behavior.")
        for line in line_iterator:
            self.add_line(line=line.rstrip("\r\n"))
            if not self.parsed.meta.is_flysight2_file and not self.options.continue_on_format_error:
                break  # stop parsing if this is not a FlySight 2 CSV file
            if self.options.metadata_only and self.parsed.meta.complete_header and self.parsed.rows:
                break  # stop parsing after the first row
        self._validate_result()
        return self.parsed

    def add_line(self, line: str) -> DataRow | None:
        """Parse a single line of the CSV file."""
        self.state.current_line_number += 1

        if self.state.current_line_number == 1:
            self.parsed.meta.is_flysight2_file = line == self.EXPECTED_HEADER
            self._error_if(not self.parsed.meta.is_flysight2_file, f"First line is not {self.EXPECTED_HEADER!r}")
            return None

        if not line.strip():
            self._error_if(not self.parsed.meta.complete_header, "Unexpected empty line.")
            logger.debug("Skipping empty line.")
            return None

        line_type, *row_fields = line.split(",")

        pattern = self.LINE_TYPE_PATTERN
        if self._error_if(not pattern.match(line_type), f"First field does not match '{pattern.pattern}'"):
            return None

        if not self.parsed.meta.complete_header:
            self._process_header_line(line_type=line_type, row_fields=row_fields)
            return None

        return self._process_data_line(line_type=line_type, row_fields=row_fields)

    def _validate_result(self) -> None:
        result = self.parsed
        self._error_if(not result.meta.vars, f"No {self.ROW_VAR} metadata found.")
        self._error_if(not result.meta.columns, "No columns found.")
        self._error_if(not result.meta.units, "No units found.")
        if result.meta.columns and result.meta.units:
            mismatched = set(result.meta.columns).symmetric_difference(result.meta.units)
            self._error_if(mismatched, "Columns/ units mismatch.")
        self._error_if(not result.meta.complete_header, "Incomplete metadata.")

        if self.options.metadata_only:
            return  # everything else does not apply to metadata-only parsing

        self._error_if(not result.rows, "No data rows found.")

    def _process_header_line(self, line_type: str, row_fields: list[str]) -> None:
        if line_type == self.ROW_VAR:
            key, value = row_fields
            self.parsed.meta.vars[key] = value
            return

        if line_type == self.ROW_COL:
            row_type, *fields = row_fields
            self.parsed.meta.columns[row_type] = fields
            return

        if line_type == self.ROW_UNIT:
            row_type, *units = row_fields
            if self._error_if(row_type not in self.parsed.meta.columns, f"Unit for non-existing {row_type}"):
                return
            for index, unit in enumerate(units):
                column = self.parsed.meta.columns[row_type][index]
                self.parsed.meta.units.setdefault(row_type, {})[column] = unit
            return

        if line_type == self.ROW_DATA:
            self._error_if(self.parsed.meta.complete_header, f"Duplicate {self.ROW_DATA} line.")
            self._error_if(bool(row_fields), f"Unexpected {self.ROW_DATA} line with fields.")
            self.parsed.meta.complete_header = True
            return

        self._error_if(True, f"Unexpected {line_type!r} before {self.ROW_DATA!r}")

    def _process_data_line(self, line_type: str, row_fields: list[str]) -> DataRow:
        self._error_if(line_type[0] != "$", f"Unexpected line type: {line_type!r}")
        sensor_name = line_type.removeprefix("$")
        data = {}
        columns = self.parsed.meta.columns[sensor_name]
        for i, value in enumerate(row_fields):
            column = columns[i]
            data[column] = self._convert_type(value)
        missing_columns = None if len(data) == len(columns) else sorted(set(columns) - set(data))
        self._error_if(missing_columns, f"Missing values for {missing_columns})")
        if line_type == self.ROW_TIME:  # update the offset datetime from the most recent $TIME row
            self.offset_datetime = self._time_data_to_offset_datetime(data)
        timestamp, offset_timestamp = self._parse_time_value(time_value=data[TIME_COL])
        meta = DataRowMeta(
            file_path=self.display_path,
            line_number=self.state.current_line_number,
            offset_timestamp=offset_timestamp,
            sensor_name=sensor_name,
            timestamp=timestamp,
            valid_offset=not self.parsed.could_not_fix_time,
        )
        row = DataRow(values=data, meta=meta)
        self.parsed.rows.append(row)
        return row

    def _convert_type(self, value: str) -> int | float | str:
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value

    def _parse_time_value(self, time_value: str | int | float) -> tuple[datetime, datetime | None]:
        if isinstance(time_value, str):  # e.g. '2023-10-08T00:35:18.800Z'
            try:
                timestamp = self._convert_string_time(time_value)
            except ValueError as e:
                self._error_if(True, f"Unexpected {TIME_COL} format: {e}")
                timestamp = self.GPS_START_DATE  # use an obviously wrong timestamp in case errors are being ignored
            return timestamp, None

        # For non-GPS data, sensors start recording before GPS lock, so time is stored as an arbitrary offset.
        if self.offset_datetime:  # We have an offset, so we can convert the time to a datetime.
            offset_datetime = self.offset_datetime
            timestamp = offset_datetime + timedelta(seconds=time_value)
            return timestamp, offset_datetime

        # we'll go back later to re-calculate the timestamps if and when we have an offset
        # use self.GPS_START_DATE as a placeholder offset for now (as it will be obvious in the data)
        self.parsed.could_not_fix_time = True
        offset_datetime = self.GPS_START_DATE
        timestamp = offset_datetime + timedelta(seconds=time_value)
        return timestamp, offset_datetime

    def _convert_string_time(self, time_value: str) -> datetime:
        negative_after_decimal_point = ".-" in time_value
        if negative_after_decimal_point:  # seems like a bug: '2023-10-08T21:36:28.-001Z'
            time_value = time_value.replace(".-", ".")
        parsed = datetime.strptime(time_value, "%Y-%m-%dT%H:%M:%S.%fZ")
        if negative_after_decimal_point:
            parsed -= timedelta(microseconds=parsed.microsecond * 2)
        assert not parsed.tzinfo, "unexpected timezone"
        return parsed

    def _time_data_to_offset_datetime(self, time_column_to_value: dict[str, Any]) -> datetime:
        """Calculate the current offset to apply to the standalone times seconds based on this GPS time row."""
        estimated_time_of_week_seconds = float(time_column_to_value[TIME_COL])
        time_of_week_seconds = float(time_column_to_value["tow"])
        week = int(time_column_to_value["week"])
        total_diff = timedelta(weeks=week) + timedelta(seconds=time_of_week_seconds)
        reference_datetime = self.GPS_START_DATE + total_diff
        offset_datetime = reference_datetime - timedelta(seconds=estimated_time_of_week_seconds)
        assert offset_datetime + timedelta(seconds=estimated_time_of_week_seconds) == reference_datetime
        return offset_datetime.replace(tzinfo=None)


def parse_csv(
    path: Path,
    *,
    options: ParserOptions,
    parser_class: type[Parser] = Parser,
) -> ParsedCSV:
    """
    Parse a single FlySight 2 CSV file.

    :param path: The path to the CSV file to parse.
    :param options: Options for the parser.
    :param parser_class: The parser class to use. Defaults to Parser.
    """
    parser = parse_csv_returning_parser(path=path, options=options, parser_class=parser_class)
    return parser.parsed


def parse_csv_returning_parser(
    path: Path,
    options: ParserOptions,
    parser_class: type[Parser] = Parser,
) -> Parser:
    """Like parse_csv, but returns the parser instead of the result."""
    path = path.resolve()
    parser = parser_class(path=path, options=options)
    with open(path, encoding="utf-8", errors="replace" if options.continue_on_format_error else "strict") as fp:
        parser.parse(fp)
    return parser


def get_parsed_for_metadata(path: Path, options: ParserOptions) -> ParsedCSV:
    """Parse the metadata and first row only from a FlySight 2 CSV file."""
    options = options.model_copy()
    options.metadata_only = True
    if options.ignore_all_format_errors:
        options.continue_on_format_error = True
    parser = parse_csv_returning_parser(path=path, options=options)
    return parser.parsed
