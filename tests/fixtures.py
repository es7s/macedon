# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
from typing import cast

import pytest
from click.testing import CliRunner

from macedon import entrypoint
from macedon.entrypoint import ClickCommand


@pytest.fixture(scope="session")
def runner():
    yield CliRunner()


@pytest.fixture(scope="function")
def ep():
    yield cast(ClickCommand, entrypoint.callback)
