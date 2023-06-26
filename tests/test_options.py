# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import re

from .fixtures import *


class TestOptions:
    def test_input_noarg(self, runner, ep):
        cp = runner.invoke(ep, args=[])
        assert cp.exception is None
        assert 'Usage:' in cp.stdout

    @pytest.mark.parametrize("args", [
        ["http://google.com"],
        ["https://google.com"],
    ])
    def test_input_strargs(self, args: list[str], runner, ep):
        cp = runner.invoke(ep, args=args)
        assert cp.exception is None
        assert re.search(R"Successful:\s+1", cp.stdout), cp.stdout

    def test_input_file_plain(self, runner, ep):
        input = (
            """
GET http://wikipedia.org
GET https://wikipedia.org
            """
        )
        cp = runner.invoke(ep, args="-f -", input=input)
        assert cp.exception is None
        assert re.search(R"Successful:\s+2", cp.stdout), cp.stdout

    def test_input_file_jetbrains_http(self, runner, ep):
        input = (
            """
GET http://yandex.ru
###
GET https://yandex.ru
            """
        )
        cp = runner.invoke(ep, args="-f -", input=input)
        assert cp.exception is None
        assert re.search(R"Successful:\s+2/2", cp.stdout), cp.stdout
