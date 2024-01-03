import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

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
from tests.common import DATA_DIR, ROOT_DIR

WRITE_EXPECTED = False  # Set this to true temporarily to update expected output files.


def _run_cli(*args: str, check_code: bool = True) -> list[str]:
    """Run the CLI."""
    result = subprocess.run(
        [sys.executable, "-m", "flysight2csv", *args],  # noqa S603
        capture_output=True,
        text=True,
        env={**os.environ, "TERM": "dumb"},
        cwd=ROOT_DIR,
    )
    if check_code and result.returncode != 0:
        pytest.fail(f"CLI failed with code {result.returncode}. stdout={result.stdout!r}, stderr={result.stderr!r}")
    if result.stderr:
        pytest.fail(f"Detected stderr: {result.stderr}. Stdout: {result.stdout}")
    return result.stdout.splitlines()


def test_help():
    """Run the CLI as a Python module."""
    expected_data_path = DATA_DIR / "cli_expected/help.txt"
    lines = _run_cli("--help")
    if WRITE_EXPECTED:
        expected_data_path.write_text("".join(f"{x}\n" for x in lines))
        pytest.fail("Expected data file was updated. Please re-run the test.")
    expected_lines = expected_data_path.read_text().splitlines()
    assert lines == expected_lines


def test_display_metadata():
    directory_path = DATA_DIR / "device1/23-12-16"
    expected_data_path = DATA_DIR / "cli_expected/device1-23-12-16-metadata.txt"
    args = [
        "--info",
        "metadata",
        "--tracebacks",
        str(directory_path.relative_to(ROOT_DIR)),
    ]
    lines = _run_cli(*args)
    if os.path.sep != "/":
        # allow tests to run on Windows without a separate expected result file
        lines = [x.replace(os.path.sep, "/") for x in lines]
    if WRITE_EXPECTED:
        expected_data_path.write_text("".join(f"{x}\n" for x in lines))
        pytest.fail("Expected data file was updated. Please re-run the test.")
    expected_lines = expected_data_path.read_text().splitlines()
    assert lines == expected_lines


@pytest.mark.parametrize(
    "args, expected",
    [
        pytest.param(
            ["fake/path"],
            ProgramParams(
                ui=UIParams(
                    continue_on_error=False, log_level="info", no_color=False, stop_on_warning=False, tracebacks=False
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
                    merged_name="MERGED",
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
            ),
            id="minimal_params",
        ),
        pytest.param(
            [
                "--info",
                "metadata",
                "tests/data/device1/23-12-16",
                "-o",
                "_tmp/output",
                "-f",
                "csv-flat",
                "--continue-on-error",
                "--continue-on-format-error",
                "--glob-patterns=**/*.CSV",
                "--no-merge",
                "--only-merge",  # conflicting merge params would raise error in real program run
                "--merged-name=MERGED2",
            ],
            ProgramParams(
                ui=UIParams(
                    continue_on_error=True, log_level="info", no_color=False, stop_on_warning=False, tracebacks=False
                ),
                finder=FinderParams(
                    files_or_directories=[Path("tests/data/device1/23-12-16")],
                    glob_patterns=["**/*.CSV"],
                    info_type=InfoTypes.metadata,
                ),
                output=OutputPathParams(
                    output_directory=Path("_tmp/output"),
                    output_path_levels=3,
                    output_path_separator="-",
                    merge=False,
                    only_merge=True,
                    merged_name="MERGED2",
                ),
                parser=ParserOptions(
                    display_path_levels=3,
                    metadata_only=False,
                    offset_datetime=None,
                    continue_on_format_error=True,
                    ignore_all_format_errors=False,
                    ignored_format_errors=None,
                ),
                reformat=ReformatParams(
                    output_format=FileFormats.csv_flat,
                    csv_dialect="flysight2csv",
                    sensors_select=None,
                    columns_select=None,
                ),
            ),
            id="various_params",
        ),
    ],
)
def test_dump_config(args: list[str], expected: Any) -> None:
    args = [*args, "--dump-config"]
    lines = _run_cli(*args)
    params = ProgramParams.model_validate_json("\n".join(lines))
    assert params == expected
