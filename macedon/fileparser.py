# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import re
import typing as t

import click
from requests.structures import CaseInsensitiveDict

from ._common import Task
from .logger import get_logger


class FileParser:
    def parse(self, file: click.File):
        try:
            yield from self._parse_jb_http_file(file)
        except Exception as e:
            get_logger().error(e)
        else:
            return
        try:
            yield from self._parse_plain(file)
        except Exception as e:
            get_logger().error(e)

    def _parse_plain(self, file: click.File) -> t.Iterable[Task]:
        while line := file.readline():
            try:
                yield Task(*self._extract_method_url(line))
            except ValueError as e:
                get_logger().error(e)
                continue

    def _parse_jb_http_file(self, file: click.File) -> t.Iterable[Task]:
        logger = get_logger()
        logger.debug("Attempting to parse jetbrains format")

        data = file.read()
        request_list = re.split(r"^###.*$\s*", data, flags=re.MULTILINE)
        request_filtered_list = [*filter(None, (r.strip() for r in request_list))]
        logger.debug(f"Detected {len(request_filtered_list)} requests")

        for idx, request in enumerate(request_filtered_list):
            logger.debug(f"Parsing request #{idx}")

            lines, last_empty_idx = self._filter_jb_http_file_lines(
                request.splitlines()
            )
            url, method = self._extract_method_url(lines[0])
            headers = CaseInsensitiveDict(
                {
                    k.strip(): v.strip()
                    for k, v in self._extract_headers(lines[1:last_empty_idx])
                }
            )
            body = None
            if last_empty_idx is not None:
                body_lines = lines[last_empty_idx:]
                body = "".join(body_lines)
                logger.debug(f"Found body ({len(body_lines)} lines, {len(body)} chars)")

            yield Task(url, method, headers, body)

    def _filter_jb_http_file_lines(
        self, lines: list[str]
    ) -> tuple[list[str], int | None]:
        last_empty_line_idx = None

        def _filter(line: str) -> bool:
            return not line.startswith("#")

        def _normalize(line: str, idx: int) -> str:
            nonlocal last_empty_line_idx
            if re.match("^\s*$", line):
                last_empty_line_idx = idx
                return ""
            return line

        filtered = [*filter(_filter, lines)]
        get_logger().debug(f"Filtered lines: {len(filtered)}")

        normalized = [_normalize(line, idx) for idx, line in enumerate(filtered)]
        get_logger().debug(f"Normalized lines: {len(normalized)}")
        get_logger().debug(f"Last empty line idx: {last_empty_line_idx}")

        return normalized, last_empty_line_idx

    def _extract_method_url(self, line: str) -> list[str, str]:
        if re.match("^([A-Z]+)\s+(https?://\S+$)", line):
            result = [*reversed(line.split(" ", 1))]
            get_logger().debug(f"Found method and url: {result}")
            return result
        raise ValueError(
            f"Invalid format, expected '{{method}} http(s)?://{{url}}', got: '{line}'"
        )

    def _extract_headers(self, lines: list[str]) -> t.Iterable[tuple[str, str]]:
        for line in lines:
            if not (m := re.match(r"^([a-zA-Z0-9_-]+):(.+)$", line)):
                continue
            header = m.group(1, 2)
            get_logger().debug(f"Found header: {header}")
            yield header


def get_parser():
    return _parser


def init_parser():
    global _parser
    _parser = FileParser()
    return _parser


_parser: FileParser | None = None
