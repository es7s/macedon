# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import threading
import time
from queue import Queue

import click
import pytermor as pt

from ._common import Options, Task, SharedState
from .fileparser import get_parser
from .logger import get_logger
from .printer import get_printer
from .worker import Worker


class Synchronizer:
    def __init__(self, url_args: tuple[str], file: tuple[click.File], options: Options):
        self._options = options
        self._shared_state = SharedState()
        self._task_pool = Queue[Task]()
        self._workers = []

        self._init_task_queue(url_args, file)
        self._init_workers()

    def run(self):
        total = self._shared_state.requests_total.value
        sep = pt.String('-'*30)
        get_printer().print_row(
            pt.String(f" Requests amount: "),
            pt.String(str(total), pt.Style(bold=True)),
        )
        get_printer().print_row(sep)
        time_before = time_after = time.time_ns()
        for worker in self._workers:
            get_logger().debug(f"Starting worker {worker}")
            worker.start()
        for worker in self._workers:
            worker.join()
        time_after = time.time_ns()

        success = self._shared_state.requests_success.value
        failed = self._shared_state.requests_failed.value
        time_total = time_after - time_before
        get_printer().print_row(sep)
        get_printer().print_row(
            pt.FixedString(f" Successful: "),
            pt.FixedString(
                str(success),
                "green" if success == total else None,
                width=6,
                align=pt.Align.RIGHT,
            ),
        )
        get_printer().print_row(
            pt.FixedString(f" Failed:     "),
            pt.FixedString(
                str(failed),
                "red" if failed > 0 else None,
                width=6,
                align=pt.Align.RIGHT,
            ),
            pt.FixedString(f"  ({100*failed/total:.1f}%)"),
        )
        get_printer().print_row(
            pt.FixedString(f" Avg time:   "),
            get_printer().format_elapsed(time_total / total),
        )
        get_printer().print_row(
            pt.FixedString(f" Total time: "),
            get_printer().format_elapsed(time_total),
        )

    def _init_task_queue(self, url_args: tuple[str], file: tuple[click.File]):
        for file_inst in file:
            try:
                for task in get_parser().parse(file_inst):
                    self._append_task(task)
            except Exception as e:
                get_logger().error(f"Failed to parse the file '{file}': {e}")
        if self._shared_state.requests_total.value > 0:
            return

        for url in url_args:
            if not url.startswith("http"):
                url = f"http://{url}"
            self._append_task(Task(url))

    def _append_task(self, task: Task):
        for _ in range(self._options.amount):
            self._task_pool.put_nowait(task)
            self._shared_state.requests_total.next()

    def _init_workers(self):
        for idx in range(self._options.threads):
            self._workers.append(
                Worker(self._options, self._task_pool, idx, self._shared_state)
            )
