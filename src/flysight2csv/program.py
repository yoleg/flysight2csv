"""
The main program logic.

Program logic is separated from the command-line interface (CLI) logic, to allow easily switching CLI/ GUI libraries.
"""
import logging
from pathlib import Path
from typing import Callable, Iterable, Iterator, Sequence

from flysight2csv.parsed import CSVMeta, ParsedCSV
from flysight2csv.parser import Parser, UnexpectedFormatError, get_parsed_for_metadata, parse_csv
from flysight2csv.program_params import FileFormats, FinderParams, InfoTypes, OutputPathParams, ProgramParams, UIParams
from flysight2csv.reformatter import NothingToWriteError, Reformatter
from flysight2csv.version import __version__

logger = logging.getLogger(__name__)
PROGRAM_NAME = "flysight2csv"
VERSION = __version__
PROGRAM_AND_VERSION = f"{PROGRAM_NAME}: {VERSION}"
GLOB_SENSOR_CSV = "**/*SENSOR.CSV"
GLOB_TRACK_CSV = "**/*TRACK.CSV"
DEFAULT_GLOB_PATTERNS = [GLOB_TRACK_CSV, GLOB_SENSOR_CSV]


class ProgramBaseError(Exception):
    """Base class for all program control flow errors."""


class FileProcessingError(ProgramBaseError):
    """Raised for exceptions that can be ignored if continue on error is specified."""

    def __init__(self, message: str, is_format_error: bool = False) -> None:
        self.message = message
        self.is_format_error = is_format_error
        super().__init__(message)


class WarningEncounteredError(ProgramBaseError):
    """Raised when a warning is encountered."""


class BadParameterError(ProgramBaseError):
    """Raised when a parameter is invalid."""


class Program:
    """
    The main program logic.

    Program logic is separated from the CLI/ GUI logic, to allow easily switching CLI/ GUI libraries.

    The program is run by calling the `run` method.

    The `print` method is used to display informational messages to the user.

    The `params` attribute contains the program parameters.
    """

    def __init__(self, params: ProgramParams, print_callback: Callable[[str], None] = print) -> None:
        self.params = params
        self.print_callback = print_callback

    def print(self, message: str) -> None:
        """Display an informational message to the user."""
        self.print_callback(message)

    def run(self) -> None:
        """Run the program."""
        logging.getLogger().setLevel(self.params.ui.log_level.upper())
        finder_params: FinderParams = self.params.finder
        paths = finder_params.files_or_directories
        non_existing_paths = [str(x) for x in paths if not x.exists()]
        if non_existing_paths:
            raise BadParameterError(f"No such file(s) or directory(ies): {non_existing_paths}")
        file_paths = list(_iter_matching_files(paths, self.params.finder.glob_patterns))
        dir_to_paths: dict[Path, list[Path]] = _map_directories_to_files(file_paths)
        if not dir_to_paths:
            display_paths = [str(x) for x in self.params.finder.files_or_directories]
            self._warn(f"No files found matching {self.params.finder.glob_patterns} in {display_paths}.")
            return
        for dir_path, paths in dir_to_paths.items():
            self._process_directory(dir_path=dir_path, paths=paths)

    def _process_directory(self, dir_path: Path, paths: list[Path]) -> None:
        all_parsed = []
        for path in paths:
            try:
                with open(path) as fd:
                    header = fd.read(1024 * 1024).splitlines(keepends=False)[0]
                is_flysight2_file = header == Parser.EXPECTED_HEADER
                if not is_flysight2_file:
                    self._warn(f"Not a FlySight 2 CSV file. Skipping: {path}")
                    continue
                logger.debug(f"Processing file: {path}")
                parsed: ParsedCSV | None = self._process_file(source_path=path)
            except Exception as e:
                self._handle_file_processing_error(e, location=str(path))  # may raise FileProcessingError
                continue
            if parsed:
                all_parsed.append(parsed)
        try:
            self._process_merge(dir_path, parsed=all_parsed, paths=paths)
        except Exception as e:
            location = f"merged file for {dir_path}"
            self._handle_file_processing_error(e, location=location)  # may raise FileProcessingError

    def _process_file(self, source_path: Path) -> ParsedCSV | None:
        output_params = self.params.output
        if not output_params.output_directory:
            self._display_paths(source_path=source_path)
            return None

        if not output_params.output_directory.is_dir():
            raise BadParameterError(f"Output directory does not exist: {output_params.output_directory}")

        target_path = self._get_target_path(source_path)
        self._display_paths(source_path=source_path, target_path=target_path)

        assert source_path.is_file(), source_path
        if target_path.is_file() and source_path.samefile(target_path):
            raise ValueError("source and target path are the same")

        if self.params.reformat.output_format == FileFormats.unchanged:
            # allow partial write in case of interrupt, to help with debugging
            _copy_file_in_chunks(source_path, target_path, chunk_size=1024 * 1024)
            return None

        parsed = parse_csv(source_path, options=self.params.parser)
        for warning in parsed.iter_warnings():
            self._warn(warning)
        if not self.params.output.only_merge:
            self._write_reformatted(parsed=parsed, target_path=target_path)
        return parsed

    def _process_merge(self, dir_path: Path, parsed: list[ParsedCSV], paths: list[Path]) -> None:
        if not self.params.output.output_directory:
            return

        if not self.params.output.merge:
            if self.params.output.only_merge:
                raise BadParameterError(f"Conflicting merge parameters leave nothing to do.")
            return

        if len(paths) == 1:
            self._warn(f"Only one file found in {dir_path}. Skipping merge.")
            return

        if not all(x.meta.vars == parsed[0].meta.vars for x in parsed):
            self._warn(f"VAR metadata mismatch in {dir_path}. Skipping merge.")
            return

        path = paths[0]
        output_params: OutputPathParams = self.params.output
        merged = sum(parsed, ParsedCSV())
        merged.sort_by_timestamp()  # TODO: this might not be accurate due to the way non-GPS sensor times are parsed
        target_path = self._get_target_path(path, rename=output_params.merged_name)
        assert target_path.name.endswith(output_params.merged_name), target_path
        self._write_reformatted(parsed=merged, target_path=target_path)
        self._display_paths(parsed=merged, source_path=path.parent / "*", target_path=target_path)

    def _display_paths(
        self,
        *,
        source_path: Path,
        target_path: Path | None = None,
        warning: str | None = None,
        parsed: ParsedCSV | None = None,
    ) -> None:
        display_type = self.params.finder.info_type
        output_format = self.params.reformat.output_format

        if display_type == InfoTypes.none:
            return
        line = f"[blue]{source_path}[/blue]"
        if target_path:
            line += f" -> [cyan]{target_path}[/cyan]"
            if output_format != FileFormats.unchanged:
                line += f" ({output_format.value})"
        if warning:
            line += f": [yellow]{warning}[/yellow]"
        self.print(line)
        if display_type == InfoTypes.path:
            return
        if display_type == InfoTypes.metadata:
            parsed = parsed or get_parsed_for_metadata(source_path, options=self.params.parser)
            self._print_meta(parsed)
            return
        raise NotImplementedError(f"Unknown display action: {display_type}")

    def _print_meta(self, parsed: ParsedCSV, indent: int = 4) -> None:
        csv_meta: CSVMeta = parsed.meta
        first_row = parsed.rows[0] if parsed.rows else None
        self.print(" " * indent + "Vars:")
        for k, v in csv_meta.vars.items():
            self.print("  " * indent + f"{k}: {v}")
        self.print(" " * indent + "Sensors/ Columns/ Units:")
        for row_type, column_to_unit in csv_meta.units.items():
            column_to_unit_string = ", ".join(f'{k} ({v or " - "})' for k, v in column_to_unit.items())
            self.print("  " * indent + f"{row_type}: {column_to_unit_string}")
        if first_row:
            self.print(" " * indent + "First data row:")
            self.print("  " * indent + f"SENSOR: {first_row.meta.sensor_name}")
            for k, v in first_row.values.items():
                self.print("  " * indent + f"{k}: {v}")
        self.print("")

    def _write_reformatted(self, parsed: ParsedCSV, target_path: Path) -> None:
        if not parsed.rows:
            assert self.params.parser.continue_on_format_error, "Otherwise an error should have been raised"
            self._warn(f"No data rows found. Not writing {target_path}.")
            return
        if not target_path.parent.is_dir():
            target_path.parent.mkdir(parents=True)
        reformatter = Reformatter(parsed=parsed, params=self.params.reformat)
        try:
            # File handle must be opened in text mode with newline='' and encoding='utf-8'.
            # See `Reformatter.write_reformatted` docstring for details.
            with open(target_path, "w", newline="", encoding="utf-8") as fd:
                reformatter.write_reformatted(fd)
        except NothingToWriteError:
            self._warn(f"No rows selected. Did not write {target_path}.")

    def _handle_file_processing_error(self, e: Exception, location: str) -> None:
        ui_params: UIParams = self.params.ui
        if isinstance(e, ProgramBaseError):
            raise
        if isinstance(e, UnexpectedFormatError):
            logger.error(f"Format error: {e}", exc_info=ui_params.tracebacks)
            if ui_params.continue_on_error:
                return
            raise FileProcessingError(f"format error in {location}", is_format_error=True) from None
        logger.error(f"Unexpected error: {type(e).__name__}: {e}", exc_info=ui_params.tracebacks)
        if ui_params.continue_on_error:
            return
        raise FileProcessingError(f"error processing {location}") from None

    def _get_target_path(self, source_path: Path, *, rename: str = "") -> Path:
        params: OutputPathParams = self.params.output
        output_directory = params.output_directory
        assert isinstance(output_directory, Path), output_directory
        name = rename or source_path.name
        parts = [*source_path.parts[-params.output_path_levels : -1], name]
        output_relative_path = params.output_path_separator.join(parts)
        target_path = output_directory / output_relative_path
        assert target_path.is_relative_to(output_directory), target_path
        return target_path

    def _warn(self, message: str) -> None:
        """Display a warning message to the user."""
        if self.params.ui.stop_on_warning:
            raise WarningEncounteredError(message)
        logger.warning(message)


def _map_directories_to_files(paths: Iterable[Path]) -> dict[Path, list[Path]]:
    """Find all files matching the glob patterns in the files or directories and group by directory."""
    dir_to_paths: dict[Path, list[Path]] = {}
    for file_path in paths:
        parent_dir: Path = file_path.resolve().absolute().parent  # avoid duplicate directories due to symlinks
        dir_to_paths.setdefault(parent_dir, []).append(file_path)
    return dir_to_paths


def _iter_matching_files(files_or_directories: Iterable[Path], glob_patterns: Sequence[str]) -> Iterator[Path]:
    """Yield all files that match any of the glob patterns in any of the files or directories."""
    for path in files_or_directories:
        if not path.is_dir():
            if path.is_file() and any(path.match(p) for p in glob_patterns):
                yield path
            continue
        for glob_pattern in glob_patterns:
            for child_path in path.glob(glob_pattern):
                if child_path.is_file():
                    yield child_path


def _copy_file_in_chunks(source_path: Path, target_path: Path, chunk_size: int) -> None:
    with open(source_path, "rb") as fd:
        with open(target_path, "wb") as fd2:
            while True:
                data = fd.read(chunk_size)
                if not data:
                    break
                fd2.write(data)
