import io
import os
from pathlib import Path

import py

from flysight2csv.program import Program
from flysight2csv.program_params import (
    FileFormats,
    FinderParams,
    InfoTypes,
    OutputPathParams,
    ParserOptions,
    ProgramParams,
    ReformatParams,
    UIParams,
)
from tests.common import DATA_DIR, read_raw_text

DEFAULTS = ProgramParams(
    ui=UIParams(
        continue_on_error=False,
        log_level="info",
        no_color=False,
        stop_on_warning=False,
        tracebacks=True,  # override default
    ),
    finder=FinderParams(
        files_or_directories=[Path("fake/path")],
        glob_patterns=["**/*TRACK.CSV", "**/*SENSOR.CSV"],
        info_type=InfoTypes.path,
    ),
    output=OutputPathParams(
        output_directory=None,
        output_path_levels=3,
        output_path_separator="-",
        merge=True,
        only_merge=False,
        merged_name="MERGED.CSV",
    ),
    parser=ParserOptions(
        display_path_levels=3,
        metadata_only=False,
        offset_datetime=None,
        continue_on_format_error=False,
        ignore_all_format_errors=False,
        ignored_format_errors=None,
    ),
    reformat=ReformatParams(
        output_format=FileFormats.unchanged,
        csv_dialect="flysight2csv",
        sensors_select=None,
        columns_select=None,
    ),
)


def test_common_reformat(tmpdir: py.path.local, monkeypatch):
    output_dir = Path(tmpdir.mkdir("output"))
    string_io = io.StringIO()
    params = DEFAULTS.model_copy(deep=True)
    params.finder.files_or_directories = [DATA_DIR / "formatted/input/"]
    params.output.output_directory = output_dir
    params.output.output_path_levels = 1
    params.parser.display_path_levels = 1
    params.reformat.output_format = FileFormats.csv_flat
    program = Program(params=params, print_callback=lambda x: string_io.write(x + "\n") and None or None)
    program.run()
    for path in output_dir.glob("**/*.*"):
        assert path.is_file()
        suffix = path.name.rsplit("-", 1)[-1]
        expected: Path = DATA_DIR / "formatted/expected/csv-flat" / suffix.lower()
        actual_lines = read_raw_text(path).splitlines(keepends=True)
        expected_lines = read_raw_text(expected).splitlines(keepends=True)
        assert actual_lines[:10] == expected_lines[:10]
    console_output = string_io.getvalue()
    console_output = console_output.replace(str(output_dir), "<output_dir>")
    console_output = console_output.replace(str(DATA_DIR), "<data_dir>")
    if os.path.sep != "/":
        # allow tests to run on Windows without a separate expected result file
        console_output = console_output.replace(os.path.sep, "/")
    assert console_output.splitlines() == [
        "[blue]<data_dir>/formatted/input/TRACK.CSV[/blue] -> " "[cyan]<output_dir>/TRACK.CSV[/cyan] (csv-flat)",
        "[blue]<data_dir>/formatted/input/SENSOR.CSV[/blue] -> " "[cyan]<output_dir>/SENSOR.CSV[/cyan] (csv-flat)",
        "[blue]<data_dir>/formatted/input/*[/blue] -> " "[cyan]<output_dir>/MERGED.CSV[/cyan] (csv-flat)",
    ]
