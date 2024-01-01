import datetime
from pathlib import Path

import pytest

from flysight2csv import parsed_csv
from flysight2csv.parsed_csv import DataRow, DataRowMeta, ParsedCSV
from flysight2csv.parser import ParserOptions, UnexpectedFormatError, parse_csv, parse_csv_returning_parser
from flysight2csv.selection import StringSelection
from tests.common import DATA_DIR

TRACK_FILES = list(DATA_DIR.glob("device*/**/TRACK.CSV"))
SENSOR_FILES = list(DATA_DIR.glob("device*/**/SENSOR.CSV"))
DEFAULT_OPTIONS = ParserOptions(strict=True, display_path_levels=3)
GPS_START_DATE = datetime.datetime(1980, 1, 6, 0, 0, 0)
SOME_DATE_BEFORE_FLYSIGHT = datetime.datetime(2000, 1, 1, 0, 0, 0)


META_FIELDS = list(parsed_csv.ROW_META_FIELDS)


def test_row_meta_fields():
    assert META_FIELDS == [
        "timestamp",
        "sensor_name",
        "file_path",
        "line_number",
        "offset_timestamp",
    ], "it should have the expected fields in the expected order"


def test_row_meta_location():
    meta = DataRowMeta(line_number=1, file_path="foo", sensor_name="bar", timestamp=datetime.datetime.now())
    assert meta.location == "foo:1", "it should have the expected location"


@pytest.mark.parametrize("path", TRACK_FILES, ids=lambda x: str(x.relative_to(DATA_DIR)))
def test_bulk_track_csv(path: Path):
    assert path.name == "TRACK.CSV", "precondition"
    expected_columns = ["time", "lat", "lon", "hMSL", "velN", "velE", "velD", "hAcc", "vAcc", "sAcc", "numSV"]
    expected_dict_fields = sorted(expected_columns + META_FIELDS)
    parsed = parse_csv(path=path, options=DEFAULT_OPTIONS)
    assert parsed.meta.columns == {"GNSS": expected_columns}, "columns are not as expected from a TRACK.CSV"
    assert parsed.warnings == [], "it should have no warnings"
    assert parsed.times_are_invalid is False, "it should have valid times"
    assert parsed.meta.complete_header is True, "it should have complete metadata"
    for i, row in enumerate(parsed.rows):
        meta = row.meta
        next_meta = parsed.rows[i + 1].meta if i + 1 < len(parsed.rows) else None
        assert not next_meta or next_meta.line_number >= meta.line_number, "line numbers should be in order"
        assert sorted(row.to_dict()) == expected_dict_fields, "it should have the expected fields"
        assert meta.timestamp > SOME_DATE_BEFORE_FLYSIGHT, "timestamp should have been parsed correctly"


@pytest.mark.parametrize("path", SENSOR_FILES, ids=lambda x: str(x.relative_to(DATA_DIR)))
def test_bulk_sensor_csv(path: Path):
    assert path.name == "SENSOR.CSV", "precondition"
    has_gps_time_rows = "$TIME" in path.read_text()
    options = ParserOptions(
        strict=False,
        display_path_levels=3,
        ignored_errors=StringSelection(
            include_patterns=[] if has_gps_time_rows else [r"No \$TIME rows available to fix timestamps"]
        ),
    )
    parsed = parse_csv(path=path, options=options)
    assert parsed.meta.columns == {
        "BARO": ["time", "pressure", "temperature"],
        "HUM": ["time", "humidity", "temperature"],
        "IMU": ["time", "wx", "wy", "wz", "ax", "ay", "az", "temperature"],
        "MAG": ["time", "x", "y", "z", "temperature"],
        "TIME": ["time", "tow", "week"],
        "VBAT": ["time", "voltage"],
    }, "columns are not as expected from a TRACK.CSV"
    assert parsed.times_are_invalid != has_gps_time_rows, "it should not set the flag correctly"
    assert parsed.meta.complete_header is True, "it should have complete metadata"
    assert parsed.warnings == [], "it should have no warnings"
    for i, row in enumerate(parsed.rows):
        meta = row.meta
        next_meta = parsed.rows[i + 1].meta if i + 1 < len(parsed.rows) else None
        assert not next_meta or next_meta.line_number >= meta.line_number, "lines should be in order"
        expected_columns = sorted(parsed.meta.columns[meta.sensor_name] + META_FIELDS)
        assert sorted(row.to_dict()) == expected_columns, "it should have the expected meta"
        assert isinstance(meta.offset_timestamp, datetime.datetime), "it should have an offset timestamp"
        if has_gps_time_rows:
            assert meta.offset_timestamp > SOME_DATE_BEFORE_FLYSIGHT, "offset should have been set correctly"
            assert meta.timestamp > SOME_DATE_BEFORE_FLYSIGHT, "offset should have been set correctly"
        else:
            assert meta.offset_timestamp == GPS_START_DATE, "offset should have been set to GPS start date"
            assert meta.timestamp.year == GPS_START_DATE.year, "offset should have been set to GPS start date"


def test_sensor_tow_rollover():
    path = DATA_DIR / "tow-rollover-SENSOR.CSV"
    parsed = parse_csv(path=path, options=DEFAULT_OPTIONS)
    assert parsed.rows == [
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/tow-rollover-SENSOR.CSV",
                line_number=10,
                sensor_name="VBAT",
                timestamp=datetime.datetime(2023, 12, 16, 23, 59, 58, 420000),
                offset_timestamp=datetime.datetime(2023, 12, 16, 21, 31, 35, 90000),
            ),
            values={"time": 8903.33, "voltage": 3.766},
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/tow-rollover-SENSOR.CSV",
                line_number=11,
                sensor_name="TIME",
                timestamp=datetime.datetime(2023, 12, 16, 23, 59, 59),
                offset_timestamp=datetime.datetime(2023, 12, 16, 21, 31, 35, 90000),
            ),
            values={"time": 8903.91, "tow": 604799.0, "week": 2292},
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/tow-rollover-SENSOR.CSV",
                line_number=12,
                sensor_name="VBAT",
                timestamp=datetime.datetime(2023, 12, 16, 23, 59, 59, 424000),
                offset_timestamp=datetime.datetime(2023, 12, 16, 21, 31, 35, 90000),
            ),
            values={"time": 8904.334, "voltage": 3.768},
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/tow-rollover-SENSOR.CSV",
                line_number=13,
                sensor_name="TIME",
                timestamp=datetime.datetime(2023, 12, 17, 0, 0),
                offset_timestamp=datetime.datetime(2023, 12, 16, 21, 31, 35, 90000),
            ),
            values={"time": 8904.91, "tow": 0.0, "week": 2293},
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/tow-rollover-SENSOR.CSV",
                line_number=14,
                sensor_name="VBAT",
                timestamp=datetime.datetime(2023, 12, 17, 0, 0, 0, 434000),
                offset_timestamp=datetime.datetime(2023, 12, 16, 21, 31, 35, 90000),
            ),
            values={"time": 8905.344, "voltage": 3.773},
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/tow-rollover-SENSOR.CSV",
                line_number=15,
                sensor_name="TIME",
                timestamp=datetime.datetime(2023, 12, 17, 0, 0, 1),
                offset_timestamp=datetime.datetime(2023, 12, 16, 21, 31, 35, 90000),
            ),
            values={"time": 8905.91, "tow": 1.0, "week": 2293},
        ),
    ], "it should have parsed the timestamps and other data correctly"


def test_track_negative_milliseconds():
    path = DATA_DIR / "negative-microsecond-TRACK.CSV"
    parsed = parse_csv(path=path, options=DEFAULT_OPTIONS)
    assert parsed.rows == [
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/negative-microsecond-TRACK.CSV",
                line_number=8,
                sensor_name="GNSS",
                timestamp=datetime.datetime(2023, 10, 8, 21, 36, 27, 798000),
                offset_timestamp=None,
            ),
            values={
                "hAcc": 48.581,
                "hMSL": -10.861,
                "lat": 38.5848559,
                "lon": -121.8540479,
                "numSV": 6,
                "sAcc": 0.86,
                "time": "2023-10-08T21:36:27.798Z",
                "vAcc": 57.75,
                "velD": 0.12,
                "velE": 0.18,
                "velN": -0.04,
            },
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/negative-microsecond-TRACK.CSV",
                line_number=9,
                sensor_name="GNSS",
                timestamp=datetime.datetime(2023, 10, 8, 21, 36, 27, 899000),
                offset_timestamp=None,
            ),
            values={
                "hAcc": 45.9,
                "hMSL": -11.04,
                "lat": 38.584851,
                "lon": -121.8540412,
                "numSV": 6,
                "sAcc": 1.01,
                "time": "2023-10-08T21:36:27.899Z",
                "vAcc": 55.623,
                "velD": 0.06,
                "velE": -0.02,
                "velN": 0.21,
            },
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/negative-microsecond-TRACK.CSV",
                line_number=10,
                sensor_name="GNSS",
                timestamp=datetime.datetime(2023, 10, 8, 21, 36, 27, 999000),
                offset_timestamp=None,
            ),
            values={
                "hAcc": 43.761,
                "hMSL": -11.093,
                "lat": 38.5848464,
                "lon": -121.8540352,
                "numSV": 6,
                "sAcc": 0.84,
                "time": "2023-10-08T21:36:28.-001Z",
                "vAcc": 53.963,
                "velD": 0.09,
                "velE": 0.11,
                "velN": -0.01,
            },
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/negative-microsecond-TRACK.CSV",
                line_number=11,
                sensor_name="GNSS",
                timestamp=datetime.datetime(2023, 10, 8, 21, 36, 28, 101000),
                offset_timestamp=None,
            ),
            values={
                "hAcc": 41.968,
                "hMSL": -11.364,
                "lat": 38.5848404,
                "lon": -121.8540306,
                "numSV": 6,
                "sAcc": 0.81,
                "time": "2023-10-08T21:36:28.101Z",
                "vAcc": 52.563,
                "velD": 0.17,
                "velE": 0.12,
                "velN": 0.04,
            },
        ),
        DataRow(
            meta=DataRowMeta(
                file_path="tests/data/negative-microsecond-TRACK.CSV",
                line_number=12,
                sensor_name="GNSS",
                timestamp=datetime.datetime(2023, 10, 8, 21, 36, 28, 182000),
                offset_timestamp=None,
            ),
            values={
                "hAcc": 70.196,
                "hMSL": -15.159,
                "lat": 38.5848734,
                "lon": -121.8539103,
                "numSV": 6,
                "sAcc": 2.03,
                "time": "2023-10-08T21:36:28.182Z",
                "vAcc": 64.019,
                "velD": 0.45,
                "velE": 0.12,
                "velN": 0.42,
            },
        ),
    ], "it should have parsed the timestamps and other data correctly"


def test_merge():
    options = ParserOptions(strict=True, display_path_levels=2)
    expected_metadata = {
        "DEVICE_ID": "0033002f4b34500b20393636",
        "FIRMWARE_VER": "v2023.07.01",
        "SESSION_ID": "ca613a35b47a65e412df9693",
    }
    path1 = DATA_DIR / "device2/23-12-16/23-36-58/SENSOR.CSV"
    path2 = DATA_DIR / "device2/23-12-16/23-36-58/TRACK.CSV"
    parsed1 = parse_csv(path=path1, options=options)
    parsed2 = parse_csv(path=path2, options=options)

    assert parsed1.meta.vars == expected_metadata, "precondition: metadata should be the same and as expected"
    assert parsed2.meta.vars == expected_metadata, "precondition: metadata should be the same and as expected"
    assert parsed1.meta.complete_header == parsed2.meta.complete_header is True, "precondition: metadata is complete"
    assert parsed1.times_are_invalid == parsed2.times_are_invalid is False, "precondition: times are valid"
    assert parsed1.warnings == parsed2.warnings == [], "precondition: no warnings"

    merged: ParsedCSV = parsed1.merge_with(parsed2, sort_by_timestamp=True, allow_vars_mismatch=False)
    assert len(parsed1.rows) + len(parsed2.rows) == len(merged.rows), "it should have the same number of rows"
    for i, row in enumerate(merged.rows):
        meta = row.meta
        next_meta = merged.rows[i + 1].meta if i + 1 < len(merged.rows) else None
        assert not next_meta or next_meta.timestamp >= meta.timestamp, "timestamps should be in order"
    assert merged.meta.paths == [path1, path2], "it should have both paths"
    assert merged.meta.display_paths == ["23-36-58/SENSOR.CSV", "23-36-58/TRACK.CSV"], "it should have both paths"
    assert merged.meta.vars == expected_metadata
    assert merged.meta.columns == {
        "BARO": ["time", "pressure", "temperature"],
        "GNSS": ["time", "lat", "lon", "hMSL", "velN", "velE", "velD", "hAcc", "vAcc", "sAcc", "numSV"],
        "HUM": ["time", "humidity", "temperature"],
        "IMU": ["time", "wx", "wy", "wz", "ax", "ay", "az", "temperature"],
        "MAG": ["time", "x", "y", "z", "temperature"],
        "TIME": ["time", "tow", "week"],
        "VBAT": ["time", "voltage"],
    }, "columns should have been merged"
    assert merged.meta.units == {
        "BARO": {"pressure": "Pa", "temperature": "deg C", "time": "s"},
        "GNSS": {
            "hAcc": "m",
            "hMSL": "m",
            "lat": "deg",
            "lon": "deg",
            "numSV": "",
            "sAcc": "m/s",
            "time": "",
            "vAcc": "m",
            "velD": "m/s",
            "velE": "m/s",
            "velN": "m/s",
        },
        "HUM": {"humidity": "percent", "temperature": "deg C", "time": "s"},
        "IMU": {
            "ax": "g",
            "ay": "g",
            "az": "g",
            "temperature": "deg C",
            "time": "s",
            "wx": "deg/s",
            "wy": "deg/s",
            "wz": "deg/s",
        },
        "MAG": {"temperature": "deg C", "time": "s", "x": "gauss", "y": "gauss", "z": "gauss"},
        "TIME": {"time": "s", "tow": "s", "week": ""},
        "VBAT": {"time": "s", "voltage": "volt"},
    }, "units should have been merged"

    assert repr(merged).startswith(
        "ParsedCSV(meta=CSVMeta(paths=(2), display_paths=['23-36-58/SENSOR.CSV', '23-36-58/TRACK.CSV'], vars="
    ), f"it should repr correctly: {merged!r}"

    assert merged.meta.complete_header is True, "it should have complete metadata"
    assert merged.times_are_invalid is False, "it should have valid times"
    assert merged.warnings == [], "it should have no warnings"


def test_incomplete_meta():
    path = DATA_DIR / "invalid/SENSOR-incomplete-meta.csv"
    options = ParserOptions(strict=False, display_path_levels=1, ignore_all_errors=True)
    parser = parse_csv_returning_parser(path, options)
    assert parser.state.ignored_messages == [
        "Unexpected '$IMU' before $DATA",
        "Unexpected '$BARO' before $DATA",
        "Unexpected '$MAG' before $DATA",
        "Unexpected '$HUM' before $DATA",
        "Incomplete metadata.",
        "No data rows found.",
    ], "it should have the expected ignored warnings"


def test_incomplete_row():
    path = DATA_DIR / "invalid/SENSOR-incomplete-row.csv"
    options = ParserOptions(strict=False, display_path_levels=1, ignore_all_errors=True)
    parser = parse_csv_returning_parser(path, options)
    assert parser.state.ignored_messages == [
        "Missing columns: ['temperature'])",
        "No $TIME rows available to fix timestamps.",
    ]


def test_not_a_csv():
    path = DATA_DIR / "invalid/not_a_csv.txt"
    options = ParserOptions(strict=False, display_path_levels=1, ignore_all_errors=True)
    parser = parse_csv_returning_parser(path, options)
    assert parser.state.ignored_messages == [
        "First line does not match '$FLYS,1'",
        r"First field does not match '^\$[A-Z]+$'",
        "No $VAR metadata found.",
        "No columns found.",
        "No units found.",
        "Incomplete metadata.",
        "No data rows found.",
    ], "it should have the expected ignored warnings"


@pytest.mark.ignore_warnings(StringSelection(include_patterns=[r".*"]))
def test_strict_mode_raises_error():
    path = DATA_DIR / "invalid/not_a_csv.txt"
    options = ParserOptions(strict=True)
    with pytest.raises(UnexpectedFormatError):
        parse_csv_returning_parser(path, options)
