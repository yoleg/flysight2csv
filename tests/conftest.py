import logging

import pytest

from flysight2csv.selection import StringSelection


@pytest.fixture(autouse=True, scope='function')
def auto_fail_on_logged_warnings_errors(caplog: pytest.LogCaptureFixture, request: pytest.FixtureRequest):
    tests_failed_before_module = request.session.testsfailed
    yield
    has_ignore_warnings_label = any(x for x in request.node.iter_markers('ignore_warnings'))
    if has_ignore_warnings_label:
        return
    tests_failed = request.session.testsfailed - tests_failed_before_module
    if tests_failed:
        return  # no need to double-fail
    messages = [x.message for x in caplog.get_records('call') if x.levelno >= logging.WARNING]
    if not messages:
        return
    for marker in request.node.iter_markers('ignore_warnings'):
        if not marker.args:
            return  # ignore all warnings
        (selection,) = marker.args
        if not isinstance(selection, StringSelection):
            raise TypeError(f"Expected a StringSelection, got {selection!r}")
        if any(selection.matches(x) for x in messages):
            return
    pytest.fail(f"Logged warnings or errors: {messages}")
