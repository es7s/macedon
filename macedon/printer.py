# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import re
import sys
import threading
from datetime import timedelta

import pytermor as pt
import requests
from pytermor import RT, Fragment

from ._common import Task, SharedState, Options
from .io import get_stdout
from .logger import get_logger


class Printer:
    COLUMN_PAD = 2
    CW_STATUS = 4
    CW_SIZE = 7
    CW_ELAPSED = 7

    SUCCESS_ST = pt.Style(fg=pt.cv.GREEN, bold=True)
    FAILURE_ST = pt.Style(fg=pt.cv.RED, bold=True)
    ERROR_ST = pt.Style(fg=pt.cv.RED, dim=True)
    REQUEST_ID_ST = pt.Style(fg=pt.cv.YELLOW)
    NO_VAL_ST = pt.Style(fg=pt.cv.GRAY_23)
    METHOD_ST = pt.Style(bold=True)

    def __init__(self, options: Options, shared_state: SharedState):
        self._options = options
        self._shared_state = shared_state
        self._lock = threading.Lock()
        self._request_table = pt.SimpleTable(sep=pt.pad(self.COLUMN_PAD))
        self._progress_table = pt.SimpleTable(sep="")

        self._size_formatter = None
        self._elapsed_formatter = None
        self._request_id_formatter = None
        self._progress_formatter = None

    def print_prolog(self):
        req_total = self._shared_state.requests_total.value
        threads = self._options.threads
        self._print_row(
            pt.Text(width=2),
            pt.Text(f"Threads:", width=12),
            pt.Text(str(threads), pt.Style(bold=True), width=6, align="right"),
        )
        self._print_row(
            pt.Text(width=2),
            pt.Text(f"Requests:", width=12),
            pt.Text(str(req_total), pt.Style(bold=True), width=6, align="right"),
        )
        self._print_separator()
        self._print_progress(True)

    def print_response(self, task: Task, response: requests.Response, request_id: int):
        size = 0
        try:
            size = len(response.content)
        except Exception:
            pass

        self._lock.acquire()
        self._print_request_result(
            self._format_status_code(response),
            self._format_size(size),
            self._format_elapsed(response.elapsed),
            self._format_request_id(request_id),
            self._format_url(task.url, task.method, None),
        )
        self._print_progress()
        self._shared_state.requests_printed.next()
        self._lock.release()

    def print_failed_request(
        self, task: Task, time_ns: int | float, request_id: int, exception: Exception
    ):
        self._lock.acquire()
        self._print_request_result(
            self._format_error(exception),
            self._format_elapsed(time_ns),
            self._format_request_id(request_id),
            self._format_url(task.url, task.method, exception),
        )
        self._print_progress()
        self._shared_state.requests_printed.next()
        self._lock.release()

    def print_epilog(self, time_delta_ns: int):
        req_total = self._shared_state.requests_total.value
        req_success = self._shared_state.requests_success.value
        req_failed = self._shared_state.requests_failed.value
        success_st = self.SUCCESS_ST if req_success == req_total else None
        failed_st = self.FAILURE_ST if req_failed > 0 else None
        avg_latency_fmtd = pt.Text("---", self.NO_VAL_ST, width=5, align="right")
        if self._shared_state.requests_latency:
            avg_latency = pt.utilmisc.median(self._shared_state.requests_latency)
            avg_latency_fmtd = self._format_elapsed(timedelta(seconds=avg_latency))

        self._reset_cursor_x()
        self._print_separator()
        self._print_row(
            pt.Text(width=2),
            pt.Text(f"Successful:", width=12),
            pt.Text(str(req_success), success_st, width=6, align="right"),
        )
        self._print_row(
            pt.Text(width=2),
            pt.Text(f"Failed:", width=12),
            pt.Text(str(req_failed), failed_st, width=6, align="right"),
            pt.Fragment(f"  ({100*req_failed/req_total:.1f}%)"),
        )
        self._print_row(
            pt.Text(width=2),
            pt.Text(f"Avg time:", width=12),
            pt.Text(width=1),
            avg_latency_fmtd,
        )
        self._print_row(
            pt.Text(width=2),
            pt.Text(f"Total time:", width=12),
            pt.Text(width=1),
            self._format_elapsed(time_delta_ns),
        )

    def _print_request_result(self, *vals: pt.IRenderable | None):
        self._reset_cursor_x()

        result = self._request_table.pass_row(*filter(None, vals))
        get_stdout().echo_rendered(result)

    def _print_progress(self, pre: bool = False):
        if not self._is_format_allowed:
            return
        self._print_row(
            pt.Text("[", width=3, align="center"),
            self._format_progress(pre),
            self._format_request_count(pre),
            pt.Text("]", width=3, align="center"),
            newline=False,
        )

    def _print_row(self, *vals: pt.IRenderable, newline: bool = True):
        stdout = get_stdout()
        result = self._progress_table.pass_row(*vals)
        stdout.echo(stdout.render(result), newline=newline)

    def _print_separator(self):
        self._print_row(pt.Text(width=25, fill="-"))

    def _reset_cursor_x(self):
        if not self._is_format_allowed:
            return
        get_stdout().echo(pt.ansi.make_set_cursor_x_abs(1).assemble(), newline=False)

    def _get_output_mode(self, opt_color: bool | None) -> pt.OutputMode:
        if opt_color is None:
            return pt.OutputMode.AUTO
        if opt_color:
            return pt.OutputMode.TRUE_COLOR
        return pt.OutputMode.NO_ANSI

    @property
    def _is_format_allowed(self) -> bool:
        return get_stdout().renderer.is_format_allowed

    def _get_max_req_id_length(self) -> int:
        return len(str(self._shared_state.requests_total.value))

    def _format_no_val(self, width: int) -> pt.Text:
        return pt.Text("---", self.NO_VAL_ST, width=width, align="center")

    def _format_status_code(self, response: requests.Response) -> pt.Text:
        string = str(response.status_code)
        fmt = self.SUCCESS_ST if response.ok else self.FAILURE_ST
        return pt.Text(string, fmt, width=self.CW_STATUS, align="right")

    def _format_error(self, exception: Exception) -> pt.Text:
        return pt.Text(
            self._get_error_type(exception),
            self.FAILURE_ST,
            width=self.CW_STATUS + self.CW_SIZE,
            align="right",
        )

    def _format_size(self, size: int) -> pt.Text:
        if not self._size_formatter:
            self._size_formatter = pt.StaticBaseFormatter(
                max_value_len=3,
                unit="b",
                unit_separator="",
                allow_negative=False,
                discrete_input=True,
                pad=True,
                color=self._is_format_allowed,
            )
        return self._size_formatter.format(size)

    def _format_elapsed(self, elapsed: timedelta | int | float) -> RT:
        if not self._elapsed_formatter:
            self._elapsed_formatter = pt.StaticBaseFormatter(
                max_value_len=3,
                allow_negative=False,
                unit="s",
                unit_separator="",
                pad=True,
                color=self._is_format_allowed,
            )
        if isinstance(elapsed, (int, float)):
            seconds = elapsed / 1e9
        elif isinstance(elapsed, timedelta):
            seconds = elapsed.total_seconds()
        else:
            get_logger().error(f"Invalid type of 'elazpsed' metric: {elapsed!r}")
            return self._format_no_val(width=self.CW_ELAPSED)
        return self._elapsed_formatter.format(seconds)

    def _format_request_id(self, request_id: int) -> pt.Text:
        if not self._options.show_id:
            return pt.Text(width=0)

        label = Fragment("#")
        result = Fragment(f"{request_id:>d}", self.REQUEST_ID_ST)
        max_width = self._get_max_req_id_length() + len(str(label.string))
        return pt.Text(label, result, width=max_width, align="right")

    def _format_progress(self, pre: bool = False) -> pt.Text:
        if not self._progress_formatter:
            self._progress_formatter = pt.StaticBaseFormatter(
                max_value_len=3,
                allow_negative=False,
                allow_fractional=False,
                unit_separator="",
                unit="%",
                pad=True,
                prefixes=[None, ""],
                color=self._is_format_allowed,
            )
        original_val = (
            100
            * (self._shared_state.requests_printed.value + (0 if pre else 1))
            / self._shared_state.requests_total.value
        )
        if original_val <= 1:
            original_val = 0.00
        result = self._progress_formatter.format(original_val)
        return result

    def _format_request_count(self, pre: bool = False) -> pt.Text:
        current = self._shared_state.requests_printed.value + (0 if pre else 1)
        total = self._shared_state.requests_total.value
        max_id_width = self._get_max_req_id_length()
        label = " "
        result = f"{label}{current:>{max_id_width}d}/{total:<{max_id_width}d}"
        return pt.Text(result, width=max_id_width * 2 + len(str(label)) + 1)

    def _format_url(
        self, url: str, method: str, exception: Exception | None
    ) -> pt.Text:
        method_len = max(len(m) for m in self._shared_state.methods)
        error = pt.Fragment(self._get_error_msg(exception), self.ERROR_ST)
        result = [
            pt.Fragment(f"{method:>{method_len}.{method_len}s} ", self.METHOD_ST),
            pt.Fragment(url + pt.pad(2)),
            error,
        ]
        return pt.Text(*result)

    def _get_error_type(self, exception: Exception | None) -> str:
        if not exception:
            return ""
        return str(exception.__class__.__qualname__)

    def _get_error_msg(self, exception: Exception | None) -> str:
        if not self._options.show_error:
            return ""
        if not exception:
            return ""
        if "Errno" in (exception_str := str(exception)):
            return re.search(r"\[Errno -?\d+][^)\']+", exception_str).group() or ""
        return ""


def get_printer() -> Printer:
    return _printer


def init_printer(options: Options, shared_state: SharedState) -> Printer:
    global _printer
    _printer = Printer(options, shared_state)

    return _printer


_printer: Printer | None = None
