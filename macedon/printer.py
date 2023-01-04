# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import sys
import threading
from datetime import timedelta

import pytermor as pt
import requests
from pytermor import StaticBaseFormatter, pad
from pytermor.common import Align as A, RT

from ._common import Task, SharedState, Options
from .logger import get_logger


class Printer:
    PAD = 2
    SPAD = 1

    CW_STATUS = 4 + PAD
    CW_SIZE = 4 + PAD
    CW_ELAPSED = 7 + PAD
    CW_REQUEST_ID = None
    CW_REQUEST_COUNT = 7 + SPAD
    CW_PROGRESS = 4 + PAD

    SUCCESS_ST = pt.Style(fg=pt.cv.GREEN, bold=True)
    FAILURE_ST = pt.Style(fg=pt.cv.RED, bold=True)
    THREAD_ID_ST = pt.Style(fg=pt.cv.GRAY)

    def __init__(self, options: Options, shared_state: SharedState):
        self._options = options
        self._terminal_width = pt.get_terminal_width()
        self._renderer = pt.SgrRenderer(self._get_output_mode(options.color))

        self._lock = threading.Lock()
        self._shared_state = shared_state

        formatter_color = self._get_formatter_color(self._renderer)
        self._size_formatter = StaticBaseFormatter(
            unit="b",
            allow_negative=False,
            discrete_input=True,
            pad=True,
            color=formatter_color,
        )
        self._elapsed_formatter = StaticBaseFormatter(
            max_value_len=3,
            allow_negative=False,
            unit="s",
            pad=True,
            color=formatter_color,
        )
        self._request_id_formatter = StaticBaseFormatter(
            max_value_len=3,
            allow_negative=False,
            allow_fractional=False,
            unit_separator="",
        )
        self._progress_formatter = StaticBaseFormatter(
            max_value_len=3,
            allow_negative=False,
            allow_fractional=False,
            unit_separator="",
            unit="%",
            pad=True,
            prefixes=[None, ""],
            color=formatter_color,
        )

    def print_response(self, task: Task, response: requests.Response, request_id: int):
        try:
            size = len(response.content)
        except Exception:
            size = 0

        self._lock.acquire()
        self.print_row(
            self._format_status_code(response),
            self._format_size(size),
            self.format_elapsed(response.elapsed),
            self._format_request_id(request_id),
            self._format_request_count(),
            self._format_progress(),
            self._format_url(task.url, task.method),
        )
        self._shared_state.requests_printed.next()
        self._lock.release()

    def print_failed_request(self, task: Task, time_ns: int|float, request_id: int):
        self._lock.acquire()
        self.print_row(
            self._format_error(self.CW_STATUS),
            self._format_no_val(self.CW_SIZE),
            self.format_elapsed(time_ns),
            self._format_request_id(request_id),
            self._format_request_count(),
            self._format_progress(),
            self._format_url(task.url, task.method),
        )
        self._shared_state.requests_printed.next()
        self._lock.release()

    def print_row(self, *vals: pt.IRenderable | None):
        result = "".join(pt.render(val, renderer=self._renderer) for val in vals)
        pt.echo(result, file=sys.stdout, flush=True)

    def _get_output_mode(self, opt_color: bool | None) -> pt.OutputMode:
        if opt_color is None:
            return pt.OutputMode.AUTO
        if opt_color:
            return pt.OutputMode.TRUE_COLOR
        return pt.OutputMode.NO_ANSI

    def _get_formatter_color(self, renderer: pt.SgrRenderer) -> bool:
        return renderer.is_format_allowed

    def _format_status_code(self, response: requests.Response) -> pt.FixedString:
        string = str(response.status_code)
        fmt = self.SUCCESS_ST if response.ok else self.FAILURE_ST
        return pt.FixedString(string, fmt, self.CW_STATUS, A.RIGHT, pad_right=self.PAD)

    def _format_error(self, width: int) -> pt.FixedString:
        string, fmt = " ERR", pt.Styles.ERROR_LABEL
        return pt.FixedString(string, fmt, width+self.PAD+1, A.LEFT, pad_right=self.PAD)

    def _format_size(self, size: int) -> pt.Text:
        return self._size_formatter.format(size) + (pad(self.PAD))

    def format_elapsed(self, elapsed: timedelta|int|float) -> RT:
        if isinstance(elapsed, (int, float)):
            seconds = elapsed / 1e9
        elif isinstance(elapsed, timedelta):
            seconds = elapsed.total_seconds()
        else:
            get_logger().error(f"Invalid type of 'elapsed' metric: {elapsed!r}")
            return self._format_no_val(width=self.CW_ELAPSED)

        return self._elapsed_formatter.format(seconds) + (pad(self.PAD))

    def _format_request_id(self, request_id: int) -> pt.FixedString:
        if not self._options.show_id:
            return pt.FixedString("")
        result = f"#{request_id:<d}"
        return pt.FixedString(result, width=self._get_req_id_column_width(), pad_right=self.SPAD)

    def _format_request_count(self) -> pt.FixedString:
        if not self._options.show_count:
            return pt.FixedString("")
        result = self._request_id_formatter.format(
            self._shared_state.requests_printed.value + 1
        ).rjust(3)
        result += "/"
        result += self._request_id_formatter.format(
            self._shared_state.requests_total.value
        ).ljust(3)
        return pt.FixedString(
            result, pt.NOOP_STYLE, self.CW_REQUEST_COUNT, pad_right=self.SPAD
        )

    def _format_progress(self) -> pt.Text:
        original_val = (
            100
            * (self._shared_state.requests_printed.value + 1)
            / self._shared_state.requests_total.value
        )

        if original_val <= 1:
            original_val = 0.00
        return self._progress_formatter.format(original_val) + pad(self.PAD)

    def _format_url(self, url: str, method: str):
        space_left = self._terminal_width - (
            self.CW_ELAPSED
            + self.CW_SIZE
            + self.CW_STATUS
            + (self._get_req_id_column_width() if self._options.show_id else 0)
            + (self.CW_REQUEST_COUNT if self._options.show_count else 0)
            + self.CW_PROGRESS
            + self.PAD
        )
        string = f"{method} {url}"
        width = max(space_left, len(method) + self.PAD)
        return pt.FixedString(
            string,
            pt.NOOP_STYLE,
            width,
            pad_right=self.PAD,
        )

    def _format_no_val(self, width: int) -> pt.FixedString:
        return pt.FixedString(
            "---",
            pt.cv.GRAY_23,
            width=width,
            align=pt.Align.CENTER,
            pad_right=self.PAD,
        )

    def _get_req_id_column_width(self) -> int:
        return 1 + len(str(self._shared_state.requests_total.value)) + self.SPAD


def get_printer() -> Printer:
    return _printer


def init_printer(options: Options, shared_state: SharedState) -> Printer:
    global _printer
    _printer = Printer(options, shared_state)

    return _printer


_printer: Printer | None = None
