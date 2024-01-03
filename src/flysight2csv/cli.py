"""Command-line interface for flysight2csv."""
import argparse
import csv
from datetime import datetime
import logging
from pathlib import Path
from typing import Any, Tuple

import rich.console
import simplejson
from rich.default_styles import DEFAULT_STYLES
import rich.logging
from rich.style import Style
from rich.theme import Theme
from rich_argparse import ArgumentDefaultsRichHelpFormatter

from flysight2csv.const import FLYSIGHT_CSV_DIALOG
from flysight2csv.program import (
    BadParameterError,
    DEFAULT_GLOB_PATTERNS,
    FileProcessingError,
    Program,
    PROGRAM_NAME,
    WarningEncounteredError,
)
from flysight2csv.program_params import FileFormats, InfoTypes, ProgramParams
from flysight2csv.version import __version__

logger = logging.getLogger(PROGRAM_NAME)
# noinspection PyUnresolvedReferences,PyProtectedMember
ArgumentGroup = argparse._ArgumentGroup

RICH_STYLES = DEFAULT_STYLES | {
    "logging.level.notset": Style(dim=True),
    "logging.level.debug": Style(color="blue", bold=True, dim=True),
    "logging.level.info": Style(color="cyan", bold=True),
    "logging.level.warning": Style(color="yellow", bold=True),
    "logging.level.error": Style(color="red", bold=True),
    "logging.level.critical": Style(color="red", bold=True, reverse=True),
}
RICH_THEME = Theme(
    RICH_STYLES,
    inherit=True,
)


# TODO: generate command-line from params dataclasses
def get_argument_parser() -> Tuple[argparse.ArgumentParser, dict[str, ArgumentGroup]]:
    """Get the argument parser."""
    # noinspection PyUnresolvedReferences
    all_info_types: list[str] = [x.value for x in InfoTypes]
    # noinspection PyUnresolvedReferences
    all_file_formats: list[str] = [x.value for x in FileFormats]

    # Create the parser
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Utility for working with FlySight 2 CSV files.",
        formatter_class=ArgumentDefaultsRichHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__, help="display the version and exit.")

    groups = {}

    # FinderParams Section
    finder_group = parser.add_argument_group("File Discovery")
    finder_group.add_argument(
        "files_or_directories",
        metavar="FILE_OR_DIR",
        type=Path,
        nargs="+",
        help="Files or directories to process.",
    )
    finder_group.add_argument(
        "--glob",
        "--glob-patterns",
        dest="glob_patterns",
        metavar="PATTERN",
        nargs="+",
        help="Glob patterns to match.",
        default=DEFAULT_GLOB_PATTERNS,
    )
    finder_group.add_argument(
        "-i",
        "--info",
        "--info-type",
        dest="info_type",
        choices=all_info_types,
        default=InfoTypes.path.value,
        help="The type of information to display about each discovered file.",
    )
    groups["finder"] = finder_group

    # ParserOptions Section
    parser_group = parser.add_argument_group("Parser Options")
    parser_group.add_argument(
        "--display-path-levels", metavar="INT", type=int, default=3, help="The number of path levels to display."
    )
    parser_group.add_argument("--metadata-only", action="store_true", help="Display metadata only.")
    parser_group.add_argument(
        "--offset-datetime",
        metavar="DATETIME",
        type=lambda s: datetime.fromisoformat(s) if s else None,
        help="Force this offset datetime instead of auto-detecting from $TIME columns.",
    )
    parser_group.add_argument(
        "--continue-on-format-error",
        action="store_true",
        help="Continue attempting to parse the file even if there are format errors.",
    )
    parser_group.add_argument("--ignore-all-format-errors", action="store_true", help="Ignore all format errors.")
    parser_group.add_argument(
        "--ignored-format-errors", metavar="MESSAGE", nargs="+", help="Ignore these format error messages."
    )
    groups["parser"] = parser_group

    output_path_group = parser.add_argument_group("Output Path")
    output_path_group.add_argument(
        "--output-directory",
        "-o",
        metavar="PATH",
        type=Path,
        default=None,
        help="Directory to copy files to. Required for the --format option.",
    )
    output_path_group.add_argument(
        "--output-path-levels",
        metavar="INT",
        type=int,
        default=3,
        help="The number of path names to join into the new file name.",
    )
    output_path_group.add_argument(
        "--output-path-separator",
        dest="output_path_separator",
        default="-",
        help="Join directories to file name with this separator. Use / to preserve directory structure.",
    )
    output_path_group.add_argument(
        "--no-merge",
        help="Do not also merge files from a single directory. Conflicts with --only-merge.",
        action="store_false",
        dest="merge",
    )
    output_path_group.add_argument(
        "--only-merge", help="Do not write non-merged files. Conflicts with --no-merge.", action="store_true"
    )
    output_path_group.add_argument(
        "--merged-name",
        metavar="NAME",
        help="The name of the merged file. NOTE: also affected by --output-path-levels.",
        default="MERGED",
    )
    groups["output"] = output_path_group

    # ReformatParams Section
    reformat_group = parser.add_argument_group("Reformatting")
    reformat_group.add_argument(
        "--format",
        "-f",
        dest="output_format",
        choices=all_file_formats,
        default=FileFormats.unchanged.value,
        help="The output file format.",
    )
    reformat_group.add_argument(
        "--csv-dialect", choices=csv.list_dialects(), default=FLYSIGHT_CSV_DIALOG, help="CSV dialect."
    )
    reformat_group.add_argument(
        "--sensors", metavar="SENSOR", dest="sensors_select", nargs="+", help="Filter data to just these sensors."
    )
    reformat_group.add_argument(
        "--columns", metavar="COLUMN", dest="columns_select", nargs="+", help="Only include these columns."
    )
    groups["reformat"] = reformat_group

    # UIParams Section
    ui_group = parser.add_argument_group("General")
    ui_group.add_argument(
        "--continue-on-error", action="store_true", help="Continue processing files if a file cannot be processed."
    )
    ui_group.add_argument(
        "--stop-on-warning", action="store_true", help="Stop processing files if a warning is encountered."
    )
    log_levels = ["debug", "info", "warning", "error", "critical"]
    ui_group.add_argument("--log-level", default="info", choices=log_levels, help="Minimal log level to display.")
    ui_group.add_argument("--no-color", action="store_true", help="Disable color output.")
    ui_group.add_argument("--tracebacks", action="store_true", help="Show exception tracebacks.")
    groups["ui"] = ui_group

    parser.add_argument("--dump-args", action="store_true", help="Print parsed arguments and exit.")
    parser.add_argument("--dump-config", action="store_true", help="Print parsed configuration (from args) and exit.")

    return parser, groups


def parse_command_line(args: list[str] | None = None) -> dict[str | None, dict[str, Any]]:
    """Parse the command line arguments."""
    parser, groups = get_argument_parser()
    parsed_args = vars(parser.parse_args(args))
    grouped_args: dict[str, dict[str, Any]] = {}
    remaining_args = parsed_args.copy()
    for key, g in groups.items():
        # noinspection PyProtectedMember
        for action in g._group_actions:
            grouped_args.setdefault(key, {})[action.dest] = parsed_args[action.dest]
            remaining_args.pop(action.dest)
    return grouped_args | {None: remaining_args}


def app(args=None):
    """Main entry point for the cli."""
    grouped_args: dict[str | None, dict[str, Any]] = parse_command_line(args)
    other_args = grouped_args.pop(None)
    if other_args["dump_args"]:
        print(simplejson.dumps(grouped_args, indent=2, default=str))
        exit(0)
    params = ProgramParams.model_validate(grouped_args)
    if other_args["dump_config"]:
        print(params.model_dump_json(indent=2))
        exit(0)
    console = rich.console.Console(theme=RICH_THEME, color_system=None if params.ui.no_color else "auto")
    handler = rich.logging.RichHandler(
        console=console,
        show_time=False,
        show_path=params.ui.tracebacks,
        markup=True,
        rich_tracebacks=False,
    )
    logging.basicConfig(
        level=logging.getLevelName(params.ui.log_level.upper()), format="%(message)s", handlers=[handler]
    )
    program = Program(params, print_callback=console.print)
    try:
        program.run()
    except FileProcessingError as e:
        logger.critical(f"Stopping due to {e}")
        if e.is_format_error:
            logger.error("To attempt to process the file anyway, use --continue-on-format-error")
        logger.error("To continue processing other files, use --continue-on-error")
        exit(2)
    except WarningEncounteredError as e:
        logger.warning(str(e))
        logger.critical("Warning encountered. Stopping due to --stop-on-warning")
        exit(2)
    except BadParameterError as e:
        logger.critical(f"Bad parameter: {e}", exc_info=params.ui.tracebacks)
        exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {type(e).__name__}: {e}", exc_info=params.ui.tracebacks)
        exit(1)


if __name__ == "__main__":
    app(
        [
            "tests/data/device1",
            "-o",
            "_temp/output",
            "--format",
            "csv-flat",
        ]
    )
