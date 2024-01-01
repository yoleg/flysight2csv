import io
from pathlib import Path

import pytest

from flysight2csv.parsed_csv import ParsedCSV
from flysight2csv.parser import ParserOptions, parse_csv
from flysight2csv.writer import Writer
from tests.common import DATA_DIR

DEFAULT_OPTIONS = ParserOptions(display_path_levels=1)
WRITE_EXPECTED = False  # Set this to true temporarily to update expected output files.


def _get_raw_text(source: Path | io.StringIO) -> str:
    if isinstance(source, io.StringIO):
        return source.getvalue()
    with open(source, newline="", encoding="utf-8") as file:
        return file.read()


def _write_raw_text(source: Path | io.StringIO, text: str) -> None:
    if isinstance(source, io.StringIO):
        source.write(text)
    else:
        with open(source, "w", newline="", encoding="utf-8") as file:
            file.write(text)


@pytest.mark.parametrize(
    "input_filenames,expected_output_filename",
    [
        pytest.param(["SENSOR.CSV"], "sensor", id="sensor"),
        pytest.param(["TRACK.CSV"], "track", id="track"),
        pytest.param(["SENSOR.CSV", "TRACK.CSV"], "merged", id="merged"),
    ],
)
@pytest.mark.parametrize("format_type", ["csv-flat", "jsonl-minimal", "jsonl-header", "jsonl-full"])
def test_write_csv_track(input_filenames, expected_output_filename: str, format_type: str):
    paths = [DATA_DIR / "formatted/input/" / x for x in input_filenames]
    expected_output_data_dir = DATA_DIR / "formatted/expected/"
    assert expected_output_data_dir.is_dir()
    extension = format_type.split("-")[0]
    expected_output_path = expected_output_data_dir / format_type / f"{expected_output_filename}.{extension}"

    merged = ParsedCSV()
    for path in paths:
        parsed = parse_csv(path, options=DEFAULT_OPTIONS)
        merged = merged.merge_with(parsed, sort_by_timestamp=False, allow_vars_mismatch=True)
    merged.sort_by_timestamp()

    string_io = io.StringIO()
    writer = Writer(merged)
    if format_type == "csv-flat":
        writer.write_csv(string_io)
    elif format_type == "jsonl-minimal":
        writer.write_json_lines(string_io, fill_nulls=False, header=False)
    elif format_type == "jsonl-header":
        writer.write_json_lines(string_io, fill_nulls=False, header=True)
    elif format_type == "jsonl-full":
        writer.write_json_lines(string_io, fill_nulls=True, header=False)
    else:
        raise NotImplementedError(extension)

    if WRITE_EXPECTED:
        expected_output_path.parent.mkdir(parents=True, exist_ok=True)
        _write_raw_text(expected_output_path, string_io.getvalue())
        pytest.fail("Expected output file was updated. Please revert WRITE_EXPECTED to False.")

    expected = _get_raw_text(expected_output_path)
    actual = _get_raw_text(string_io)
    assert actual == expected
