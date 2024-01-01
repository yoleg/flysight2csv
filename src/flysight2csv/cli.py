"""
flysight2csv command line interface.

Still a work in progress.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from pathlib import Path
import sys
import traceback
from typing import Annotated, Any, Iterable, Optional

from rich import print as color_print
from rich.logging import RichHandler
import typer
from typer import Argument, Option

from flysight2csv.csv import FLYSIGHT_CSV_DIALOG
from flysight2csv.finder import iter_matching_files
from flysight2csv.parsed_csv import CSVMeta
from flysight2csv.parser import ParserOptions, UnexpectedFormatError, get_metadata, parse_csv
from flysight2csv.selection import StringSelection
from flysight2csv.version import __version__
from flysight2csv.writer import NothingToWriteError, Writer

PROGRAM_NAME = 'flysight2csv'
GLOB_SENSOR_CSV = '**/*SENSOR.CSV'
GLOB_TRACK_CSV = '**/*TRACK.CSV'
DEFAULT_GLOB_PATTERNS = [GLOB_TRACK_CSV, GLOB_SENSOR_CSV]

app = typer.Typer(name=PROGRAM_NAME, pretty_exceptions_enable=False)
logger = logging.getLogger(PROGRAM_NAME)


def print(*objects: Any) -> None:
    """Print to stdout with color."""
    color_print(*objects, flush=True, file=sys.stdout)


def _version_callback(value: bool) -> None:
    if value:
        print(f'{PROGRAM_NAME}: {__version__}')
        raise typer.Exit()


class _DisplayAction(str, Enum):
    none = 'none'
    path = 'path'
    meta = 'meta'


class _FileFormat(str, Enum):
    original = 'original'
    csv_flat = 'csv-flat'
    json_lines_minimal = 'json-lines-minimal'
    json_lines_header = 'json-lines-header'
    json_lines_full = 'json-lines-full'


# noinspection PyUnusedLocal,PyShadowingBuiltins
@app.command()
def flysight2csv(
    # display options
    display_type: Annotated[_DisplayAction, Option('--display', '-d', help='what to display')] = _DisplayAction.path,
    tracebacks: bool = False,
    # finding files
    files_or_directories: list[Path] = Argument(),
    glob_patterns: Optional[list[str]] = Option(
        None,
        '--glob',
        show_default=False,
        help=f'Glob patterns to match. Defaults to: {" ".join(DEFAULT_GLOB_PATTERNS)}.',
    ),
    sort_paths: bool = True,
    # file parser options
    offset_datetime: Optional[str] = None,
    continue_on_error: bool = False,
    ignore_all_errors: bool = False,
    error_ignore_patterns: Optional[list[str]] = None,
    display_path_levels: Annotated[
        int, Option(help='The number of path names to display in converted files. Set to 0 for the full path.')
    ] = 3,
    # file copy options
    output_directory: Annotated[
        Optional[Path],
        Option(
            '--output-directory', '-o', help='Output directory. If provided, the discovered files will be copied here.'
        ),
    ] = None,
    format: Annotated[_FileFormat, Option('--format', '-f', help='the output file format')] = _FileFormat.original,
    output_path_levels: Annotated[int, Option(help='The number of path names to join into the new file name.')] = 3,
    output_path_separator: Annotated[
        str,
        Option(
            '--sep', help='Join directories to file name with this separator. Use / to preserve directory structure'
        ),
    ] = '-',
    csv_dialect: str = FLYSIGHT_CSV_DIALOG,
    columns: Optional[list[str]] = None,  # TODO: allow patterns/ exclusions
    sensors: Optional[list[str]] = None,  # TODO: allow patterns/ exclusions
    # logging
    log_level: Annotated[str, Option('--log-level', '-L')] = 'info',
    log_format: str = '%(message)s',
    log_date_format: str = '%Y-%m-%d %H:%M:%S',
    # misc
    version: Annotated[Optional[bool], Option("--version", is_eager=True, callback=_version_callback)] = None,
) -> None:
    """Utility for finding and converting FlySight 2 CSV files."""
    logging.basicConfig(
        level=logging.getLevelName(log_level.upper()),
        format=log_format,
        datefmt=log_date_format,
        handlers=[RichHandler()],
    )
    glob_patterns = glob_patterns or DEFAULT_GLOB_PATTERNS.copy()
    parser_options = ParserOptions(
        display_path_levels=display_path_levels,
        ignored_errors=StringSelection(include_patterns=error_ignore_patterns) or None,
        ignore_all_errors=ignore_all_errors,
        offset_datetime=offset_datetime and datetime.fromisoformat(offset_datetime) or None,
        strict=not continue_on_error,
        metadata_only=not output_directory,
    )
    if nonexisting_files_or_directories := [str(p) for p in files_or_directories if not p.exists()]:
        raise typer.BadParameter(f'Files or directories do not exist: {nonexisting_files_or_directories}')
    params = _Params(
        format=format,
        display_type=display_type,
        parser_options=parser_options,
        output_directory=output_directory,
        output_path_levels=output_path_levels,
        output_path_separator=output_path_separator,
        sensors_select=StringSelection(include_values=sensors) if sensors else None,
        columns_select=StringSelection(include_values=columns) if columns else None,
    )
    paths_iterable: Iterable[Path] = iter_matching_files(files_or_directories, glob_patterns=glob_patterns)
    if sort_paths:
        paths_iterable = sorted(paths_iterable)
    for path in paths_iterable:
        csv_meta = get_metadata(path=path, options=parser_options, ignore_all_errors=ignore_all_errors)
        if not csv_meta.complete_header:
            continue
        try:
            _process_file(params, source_path=path, csv_meta=csv_meta)
        except typer.Exit:
            raise
        except Exception as e:
            print(f'[red]    Error processing file: {type(e).__name__}: {e}[/red]')
            if continue_on_error:
                if tracebacks:
                    lines = [f'  {line}' for line in traceback.format_exception(e)]
                    print(f'[red]{"".join(lines)}[/red]')
                continue
            if tracebacks:
                raise
            typer.Exit(code=1)


@dataclass
class _Params:
    format: _FileFormat
    display_type: _DisplayAction
    parser_options: ParserOptions
    output_directory: Path | None
    output_path_levels: int = 3
    output_path_separator: str = '-'
    sensors_select: StringSelection | None = None
    columns_select: StringSelection | None = None
    csv_dialect: str = FLYSIGHT_CSV_DIALOG


def _display_paths(
    params: _Params,
    csv_meta: CSVMeta,
    *,
    source_path: Path,
    target_path: Path | None = None,
    warning: str | None = None,
) -> None:
    source_path = source_path if source_path.is_absolute() else source_path.absolute().relative_to(Path.cwd())
    target_path = target_path and (
        target_path if target_path.is_absolute() else target_path.absolute().relative_to(Path.cwd())
    )
    display_type = params.display_type
    if display_type == _DisplayAction.none:
        return
    line = f'[blue]{source_path}[/blue]'
    if target_path:
        line += f' -> [cyan]{target_path}[/cyan]'
        if params.format != _FileFormat.original:
            line += f' ({params.format.value})'
    if warning:
        line += f': [yellow]{warning}[/yellow]'
    print(line)
    if display_type == _DisplayAction.path:
        return
    if display_type == _DisplayAction.meta:
        _print_meta(csv_meta)
        return
    raise NotImplementedError(f'Unknown display action: {display_type}')


def _process_file(params: _Params, source_path: Path, csv_meta: CSVMeta) -> None:
    if not params.output_directory:
        _display_paths(params, csv_meta=csv_meta, source_path=source_path)
        return

    if not params.output_directory.is_dir():
        raise typer.BadParameter(f'Output directory does not exist: {params.output_directory}')

    output_relative_path = params.output_path_separator.join(source_path.parts[-params.output_path_levels :])
    target_path = params.output_directory / output_relative_path
    assert target_path.is_relative_to(params.output_directory), target_path
    _display_paths(
        params=params,
        csv_meta=csv_meta,
        source_path=source_path,
        target_path=target_path,
    )
    try:
        _convert_file(params, source_path=source_path, target_path=target_path)
    except NothingToWriteError:
        logger.warning('No rows selected. Not writing file.')


def _convert_file(params: _Params, source_path: Path, target_path: Path) -> None:
    assert source_path.is_file(), source_path
    if target_path.is_file() and source_path.samefile(target_path):
        raise ValueError('source and target path are the same')

    if params.format == _FileFormat.original:
        with open(source_path, 'rb') as fd:
            with open(target_path, 'wb') as fd2:
                while True:
                    data = fd.read(1024 * 1024)
                    if not data:
                        break
                    fd2.write(data)
        return

    try:
        parsed = parse_csv(source_path, options=params.parser_options)
    except UnexpectedFormatError:
        print('[red]Error parsing CSV file. See log messages above. To continue, use --continue-on-error.[/red]')
        raise typer.Exit(code=1) from None

    writer = Writer(parsed=parsed, columns=params.columns_select, sensors=params.sensors_select)

    if not target_path.parent.is_dir():
        target_path.parent.mkdir(parents=True)
    with open(target_path, 'w', newline='', encoding='utf-8') as fd:
        if params.format == _FileFormat.csv_flat:
            writer.write_csv(fd, dialect=params.csv_dialect)
        elif params.format == _FileFormat.json_lines_minimal:
            writer.write_json_lines(fd, header=False, fill_nulls=False)
        elif params.format == _FileFormat.json_lines_header:
            writer.write_json_lines(fd, header=True, fill_nulls=False)
        elif params.format == _FileFormat.json_lines_full:
            writer.write_json_lines(fd, header=False, fill_nulls=True)
        else:
            raise NotImplementedError(f'Not-implemented format: {params.format}')


def _print_meta(csv_meta: CSVMeta, indent: int = 4) -> None:
    print(' ' * indent + 'Vars:')
    for k, v in csv_meta.vars.items():
        print('  ' * indent + f'{k}: {v}')
    print(' ' * indent + 'Columns:')
    for row_type, column_to_unit in csv_meta.units.items():
        column_to_unit_string = ', '.join(f'{k} ({v or " - "})' for k, v in column_to_unit.items())
        print('  ' * indent + f'{row_type}: {column_to_unit_string}')
    print('')
