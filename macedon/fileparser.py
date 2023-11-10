# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import re
import typing as t

from requests.structures import CaseInsensitiveDict

from ._common import Task
from .logger import get_logger


class FileParser:
    def parse(self, file: t.TextIO):
        data = file.read()
        try:
            yield from self._parse(data, file.name)
        except Exception as e:
            raise RuntimeError(f"Failed to parse file '{file}'") from e

    def _parse(self, data: str, file_name: str) -> t.Iterable[Task]:
        get_logger().trace(f"Parsing {file_name!r}" + '\n' + data)

        lines = data.splitlines()
        if all(re.fullmatch(R"^\s*$|^\S+\s+\S+$", line) for line in lines):
            yield from self._parse_plain(lines)
        else:
            yield from self._parse_jb_http_file(data)

    def _parse_plain(self, lines: list[str]) -> t.Iterable[Task]:
        for line in lines:
            if line.startswith("#"):
                continue
            try:
                yield Task(*self._extract_method_url(line))
            except ValueError as e:
                get_logger().exception(e)
                continue

    def _parse_jb_http_file(self, data: str) -> t.Iterable[Task]:
        request_list = re.split(r"^###.*$\s*", data, flags=re.MULTILINE)
        request_filtered_list = [*filter(None, (r.strip() for r in request_list))]

        for idx, request in enumerate(request_filtered_list):
            lines, last_empty_idx = self._filter_jb_http_file_lines(request.splitlines())
            url, method = self._extract_method_url(lines[0])
            headers = CaseInsensitiveDict(
                {k.strip(): v.strip() for k, v in self._extract_headers(lines[1:last_empty_idx])}
            )
            body = None
            if last_empty_idx is not None:
                body_lines = lines[last_empty_idx:]
                body = "".join(body_lines)

            yield Task(url, method, headers, body)

    def _filter_jb_http_file_lines(
        self,
        lines: list[str],
    ) -> tuple[list[str], int | None]:
        last_empty_line_idx = None

        def _filter(line: str) -> bool:
            return not line.startswith("#")

        def _normalize(line: str, idx: int) -> str:
            nonlocal last_empty_line_idx
            if re.match(r"^\s*$", line):
                last_empty_line_idx = idx
                return ""
            return line

        filtered = [*filter(_filter, lines)]
        normalized = [_normalize(line, idx) for idx, line in enumerate(filtered)]

        return normalized, last_empty_line_idx

    def _extract_method_url(self, line: str) -> list[str, str]:
        if re.match(r"^([A-Z]+)\s+(https?://\S+$)", line):
            result = [*reversed(line.split(" ", 1))]
            return result
        raise ValueError(f"Invalid format, expected '{{method}} http(s)?://{{url}}', got: '{line}'")

    def _extract_headers(self, lines: list[str]) -> t.Iterable[tuple[str, str]]:
        for line in lines:
            if not (m := re.match(r"^([a-zA-Z0-9_-]+):(.+)$", line)):
                continue
            header = m.group(1, 2)
            yield header


def get_parser():
    return _parser


def init_parser():
    global _parser
    _parser = FileParser()
    return _parser


def destroy_parser():
    global _parser
    _parser = None


_parser: FileParser | None = None
