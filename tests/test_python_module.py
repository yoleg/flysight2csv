import subprocess
import sys


def test_can_run_as_python_module():
    """Run the CLI as a Python module."""
    result = subprocess.run(
        [sys.executable, "-m", "flysight2csv", "--help"],  # noqa S603,S607
        check=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert b"flysight2csv [OPTIONS]" in result.stdout
