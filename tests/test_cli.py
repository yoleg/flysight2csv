from pathlib import Path
import re
import sys

import pytest
from typer.testing import CliRunner

from flysight2csv.cli import app
from tests.common import DATA_DIR

runner = CliRunner()


@pytest.mark.skip(reason="TODO: fix for CI/CD")
def test_help():
    """The help message includes the CLI name."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    expected_lines_start = [
        "                                                                               ",
        " Usage: flysight2csv [OPTIONS] FILES_OR_DIRECTORIES...                         ",
        "                                                                               ",
        " Utility for finding and converting FlySight 2 CSV files.                      ",
        "                                                                               ",
    ]
    actual_lines = result.stdout.splitlines(keepends=False)
    assert actual_lines[: len(expected_lines_start)] == expected_lines_start


def test_version():
    """The version is in the output."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert re.match(r"^flysight2csv: \d+\.\d+\.\d+$", result.stdout)


@pytest.mark.skip(reason="TODO: fix for CI/CD")
def test_display_metadata():
    directory_path = DATA_DIR / "device1/23-12-16"
    args = [
        "-d",
        "meta",
        str(directory_path.relative_to(Path.cwd())),
    ]
    result = runner.invoke(
        app,
        args,
    )
    assert result.exit_code == 0
    stdout = result.stdout
    # convert path separators to allow tests to run on Windows
    if sys.platform == "win32":
        stdout = stdout.replace("\\", "/")
    lines = stdout.splitlines(keepends=False)
    assert lines == [
        "data/device1/23-12-16/23-21-02/SENSOR.CSV",
        "    Vars:",
        "        FIRMWARE_VER: v2023.07.01",
        "        DEVICE_ID: 003b00555752501920313652",
        "        SESSION_ID: 1c19e8c738d16fd9108c3ea9",
        "    Columns:",
        "        BARO: time (s), pressure (Pa), temperature (deg C)",
        "        HUM: time (s), humidity (percent), temperature (deg C)",
        "        MAG: time (s), x (gauss), y (gauss), z (gauss), temperature (deg C)",
        "        IMU: time (s), wx (deg/s), wy (deg/s), wz (deg/s), ax (g), ay (g), " "az ",
        "(g), temperature (deg C)",
        "        TIME: time (s), tow (s), week ( - )",
        "        VBAT: time (s), voltage (volt)",
        "",
        "data/device1/23-12-16/23-21-02/TRACK.CSV",
        "    Vars:",
        "        FIRMWARE_VER: v2023.07.01",
        "        DEVICE_ID: 003b00555752501920313652",
        "        SESSION_ID: 1c19e8c738d16fd9108c3ea9",
        "    Columns:",
        "        GNSS: time ( - ), lat (deg), lon (deg), hMSL (m), velN (m/s), velE ",
        "(m/s), velD (m/s), hAcc (m), vAcc (m), sAcc (m/s), numSV ( - )",
        "",
        "data/device1/23-12-16/23-37-27/SENSOR.CSV",
        "    Vars:",
        "        FIRMWARE_VER: v2023.07.01",
        "        DEVICE_ID: 003b00555752501920313652",
        "        SESSION_ID: 41a736c9ef9aaacacf327db0",
        "    Columns:",
        "        BARO: time (s), pressure (Pa), temperature (deg C)",
        "        HUM: time (s), humidity (percent), temperature (deg C)",
        "        MAG: time (s), x (gauss), y (gauss), z (gauss), temperature (deg C)",
        "        IMU: time (s), wx (deg/s), wy (deg/s), wz (deg/s), ax (g), ay (g), " "az ",
        "(g), temperature (deg C)",
        "        TIME: time (s), tow (s), week ( - )",
        "        VBAT: time (s), voltage (volt)",
        "",
        "data/device1/23-12-16/23-37-27/TRACK.CSV",
        "    Vars:",
        "        FIRMWARE_VER: v2023.07.01",
        "        DEVICE_ID: 003b00555752501920313652",
        "        SESSION_ID: 41a736c9ef9aaacacf327db0",
        "    Columns:",
        "        GNSS: time ( - ), lat (deg), lon (deg), hMSL (m), velN (m/s), velE ",
        "(m/s), velD (m/s), hAcc (m), vAcc (m), sAcc (m/s), numSV ( - )",
        "",
    ]
