# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2024 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
from re import Pattern
from typing import cast

import pytest
from click.testing import CliRunner as ClickCliRunner, Result

from macedon import entrypoint
from macedon.entrypoint import ClickCommand


class CliRunner(ClickCliRunner):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._last_result: Result | None = None

    def invoke(self, *args, no_errors: bool = None, **kwargs) -> Result:
        self._last_result = super().invoke(*args, **kwargs)
        if no_errors is not None:
            if no_errors:
                self.assert_no_errors()
            else:
                self.assert_errors()
        return self._last_result

    def assert_no_errors(self):
        assert self._last_result.exception is None
        assert self._last_result.exit_code == 0

    def assert_errors(self):
        assert self._last_result.exception or self._last_result.exit_code

    def assert_stdout(self, subj: str | Pattern):
        self._assert_stream_contains(self._last_result.stdout, subj)

    def assert_stderr(self, subj: str | Pattern):
        self._assert_stream_contains(self._last_result.stderr, subj)

    def _assert_stream_contains(self, stream: str, subj: str | Pattern):
        if isinstance(subj, Pattern):
            assert subj.search(stream)
        else:
            assert subj in stream


@pytest.fixture(scope="function")
def runner():
    yield CliRunner(mix_stderr=False)


@pytest.fixture(scope="session")
def ep():
    yield cast(ClickCommand, entrypoint.callback)
