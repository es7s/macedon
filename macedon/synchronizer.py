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
    def __init__(
        self,
        url_args: tuple[str],
        file: tuple[click.File],
        options: Options,
        shared_state: SharedState,
    ):
        self._options = options
        self._shared_state = shared_state
        self._task_pool = Queue[Task]()
        self._workers = []

        try:
            self._init_task_queue(url_args, file)
            self._init_workers()
        except Exception as e:
            get_logger().critical(e)
            exit(1)

    def run(self):
        printer = get_printer()
        printer.print_prolog()
        time_before = time.time_ns()

        for worker in self._workers:
            get_logger().debug(f"Starting worker {worker}")
            worker.start()
        for worker in self._workers:
            worker.join()

        time_after = time.time_ns()
        self._shared_state.requests_latency.sort()
        printer.print_epilog(time_after - time_before)

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

        if self._shared_state.requests_total.value == 0:
            raise ValueError("No urls provided")

    def _append_task(self, task: Task):
        self._shared_state.methods.add(task.method)
        for _ in range(self._options.amount):
            self._task_pool.put_nowait(task)
            self._shared_state.requests_total.next()

    def _init_workers(self):
        self._shared_state.worker_states = ["init"] * self._options.threads
        for idx in range(self._options.threads):
            self._workers.append(
                Worker(self._options, self._task_pool, idx, self._shared_state)
            )
