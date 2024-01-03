import io
import os

import pytest

from flysight2csv.parsed import ParsedCSV
from flysight2csv.parser import parse_csv
from flysight2csv.program_params import EXTENSIONS, FileFormats, ParserOptions, ReformatParams
from flysight2csv.reformatter import Reformatter
from tests.common import DATA_DIR, read_raw_text, write_raw_text

WRITE_EXPECTED = False  # Set this to true temporarily to update expected output files.

PARSER_OPTIONS = ParserOptions(
    display_path_levels=1,
    metadata_only=False,
    offset_datetime=None,
    continue_on_format_error=False,
    ignore_all_format_errors=False,
    ignored_format_errors=None,
)
DEFAULT_PARAMS = ReformatParams(
    output_format=FileFormats.csv_flat,
    csv_dialect="excel",
    sensors_select=None,
    columns_select=None,
)


@pytest.mark.parametrize(
    "input_filenames,expected_output_filename",
    [
        pytest.param(["SENSOR.CSV"], "sensor", id="sensor"),
        pytest.param(["TRACK.CSV"], "track", id="track"),
        pytest.param(["TRACK.CSV", "SENSOR.CSV"], "merged", id="merged"),
    ],
)
@pytest.mark.parametrize("format_type", [x for x in FileFormats if x != FileFormats.unchanged])
def test_write_csv(input_filenames: list[str], expected_output_filename: str, format_type: FileFormats):
    paths = [DATA_DIR / "formatted/input/" / x for x in input_filenames]
    expected_output_data_dir = DATA_DIR / "formatted/expected/"
    assert expected_output_data_dir.is_dir()
    extension = EXTENSIONS[format_type]
    expected_output_path = expected_output_data_dir / format_type.value / f"{expected_output_filename}{extension}"

    merged = ParsedCSV()
    for path in paths:
        parsed = parse_csv(path, options=PARSER_OPTIONS)
        merged = merged.merge_with(parsed, sort_by_timestamp=False, allow_vars_mismatch=True)
    merged.sort_by_timestamp()

    string_io = io.StringIO()
    writer = Reformatter(merged, params=DEFAULT_PARAMS)
    if format_type == FileFormats.csv_flat:
        writer.write_csv(string_io)
    elif format_type == FileFormats.json_lines_minimal:
        writer.write_json_lines(string_io, fill_nulls=False, header=False)
    elif format_type == FileFormats.json_lines_header:
        writer.write_json_lines(string_io, fill_nulls=False, header=True)
    elif format_type == FileFormats.json_lines_full:
        writer.write_json_lines(string_io, fill_nulls=True, header=False)
    else:
        raise NotImplementedError(extension)

    if WRITE_EXPECTED:
        expected_output_path.parent.mkdir(parents=True, exist_ok=True)
        write_raw_text(expected_output_path, string_io.getvalue())
        pytest.fail("Expected output file was updated. Please revert WRITE_EXPECTED to False.")

    expected = read_raw_text(expected_output_path)
    if extension == ".csv":  # CSV files by default write \r\n on any OS. TODO: should this change?
        assert "\r\n" in expected
    else:
        expected = expected.replace("\r\n", os.linesep)
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = read_raw_text(string_io).splitlines(keepends=True)
    assert actual_lines[:10] == expected_lines[:10]  # pre-check to avoid printing large diffs in most cases
    assert actual_lines == expected_lines
