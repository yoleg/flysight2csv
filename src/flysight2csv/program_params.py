"""Data classes representing the user-configurable program parameters."""
from __future__ import annotations

from enum import Enum
from pathlib import Path, PurePath
from typing import Any

from pydantic import BaseModel, Field, NaiveDatetime, field_validator

from flysight2csv.selection import StringSelection


class BaseParams(BaseModel):
    """A base class for parameter dataclasses."""

    pass


class ProgramParams(BaseParams):
    """The configurable parameters for the program."""

    ui: UIParams
    finder: FinderParams
    output: OutputPathParams
    parser: ParserOptions
    reformat: ReformatParams


class UIParams(BaseParams):
    """The configurable parameters for logging and information."""

    continue_on_error: bool = Field(description="Continue processing files if a file cannot be processed.")
    log_level: str
    no_color: bool
    stop_on_warning: bool = Field(description="Stop processing files if a warning is encountered.")
    tracebacks: bool


class FinderParams(BaseParams):
    """The configurable parameters for locating the source files."""

    files_or_directories: list[Path]
    glob_patterns: list[str]
    info_type: InfoTypes


class ReformatParams(BaseParams):
    """The configurable parameters for reformatting the files."""

    output_format: FileFormats
    csv_dialect: str
    sensors_select: StringSelection | None
    columns_select: StringSelection | None

    @field_validator("sensors_select", "columns_select", mode="before")
    @classmethod
    def _convert_list_to_selection(cls, value: Any) -> Any:
        if value and isinstance(value, list):
            return StringSelection(include_values=value)
        return value


class OutputPathParams(BaseParams):
    """The configurable parameters for the output path."""

    output_directory: Path | None
    output_path_levels: int
    output_path_separator: str
    merge: bool
    only_merge: bool
    merged_name: str


class ParserOptions(BaseParams):
    """
    Configurable options for a FlySight 2 CSV parser.

    :param ignored_format_errors: Ignore format errors if they match any of these regular expressions.
    :param offset_datetime: A datetime to use as the offset for non-GPS timestamps. If not provided, will attempt to
                            auto-detected from $TIME fields.
    :param continue_on_format_error: Keep trying to parse the file even if there are format errors.
    :param metadata_only: Only parse the metadata and column definitions, not the data rows.
    :param display_path_levels: The number of path levels to display in messages and outputs. Use 0 for full
                                paths, 1 for filenames only, 2 for filenames and parent directory names, etc....
    """

    display_path_levels: int = Field(ge=0)
    metadata_only: bool
    offset_datetime: NaiveDatetime | None
    continue_on_format_error: bool
    ignore_all_format_errors: bool
    ignored_format_errors: StringSelection | None

    @field_validator("ignored_format_errors", mode="before")
    @classmethod
    def _convert_list_to_selection(cls, value: Any) -> Any:
        if value and isinstance(value, list):
            return StringSelection(include_values=value)
        return value or None

    def format_display_path(self, path: str | PurePath) -> str:
        """Format a path for display in messages and outputs."""
        if self.display_path_levels <= 0:
            return str(path)
        return str("/".join(PurePath(path).parts[-self.display_path_levels :]))


class PythonReprEnum(Enum):
    """An Enum that uses a Python representation."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.name}"


class InfoTypes(str, PythonReprEnum):
    """The types of information that can be displayed about the files."""

    none = "none"
    path = "path"
    metadata = "metadata"


class FileFormats(str, PythonReprEnum):
    """The file formats that are available."""

    unchanged = "unchanged"
    csv_flat = "csv-flat"
    json_lines_minimal = "json-lines-minimal"
    json_lines_header = "json-lines-header"
    json_lines_full = "json-lines-full"
