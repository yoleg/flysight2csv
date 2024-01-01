import subprocess
import sys

from flysight2csv.version import __version__


def test_can_run_as_python_module():
    """Run the CLI as a Python module."""
    result = subprocess.run(
        [sys.executable, "-m", "flysight2csv", "--version"],  # noqa S603
        check=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert result.stdout.decode().splitlines() == [__version__]
