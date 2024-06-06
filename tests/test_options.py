# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2023-2024 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import re

from .fixtures import *


class TestOptions:
    def test_input_noarg(self, runner, ep):
        runner.invoke(ep, args=[], no_errors=True)
        runner.assert_stdout("Usage:")

    @pytest.mark.parametrize(
        "args",
        [
            ["http://google.com"],
            ["https://google.com"],
        ],
    )
    def test_input_strargs(self, args: list[str], runner, ep):
        runner.invoke(ep, args=args, no_errors=True)
        runner.assert_stdout(re.compile(R"Successful:\s+1"))

    def test_input_file_plain(self, runner, ep):
        input = """
            GET http://wikipedia.org
            GET https://wikipedia.org
        """
        runner.invoke(ep, args="-f -", input=input, no_errors=True)
        runner.assert_stdout(re.compile(R"Successful:\s+2"))

    def test_input_file_jetbrains_http_comments(self, runner, ep):
        input = "\n".join(["GET http://yandex.ru", "###", "GET https://yandex.ru"])
        runner.invoke(ep, args="-f -", input=input, no_errors=True)
        runner.assert_stdout(re.compile(R"Successful:\s+2/2"))

    def test_input_file_jetbrains_http_no_method(self, runner, ep):
        input = "https://2ip.ru"
        runner.invoke(ep, args="-f -", input=input, no_errors=True)
        runner.assert_stdout(re.compile(R"Successful:\s+1"))

    # @TODO run `whoami` as a docker container for tests?
    def test_input_file_jetbrains_http_header(self, runner, ep):
        input = """
            GET https://whoami.dlup.link
            Accept: */*
            User-Agent: curl/7.68.0
            Accept-Encoding: gzip
        """
        runner.invoke(ep, args="-f - -vv", input=input, no_errors=True)
        runner.assert_stdout("200")
        runner.assert_stderr("curl/7.68.0")

    # @TODO same
    def test_input_file_jetbrains_http_body(self, runner, ep):
        input = """
            POST https://rcv.dlup.link/test/post
            Content-Type: application/json
            
            {"key": "val"}
        """
        runner.invoke(ep, args="-f - -vv", input=input, no_errors=True)
        runner.assert_stdout("200")
        runner.assert_stderr("key=val")

    def test_delay(self, runner, ep):
        runner.invoke(ep, args="-d 1 https://2ip.ru", no_errors=True)
        runner.assert_stdout("200")
