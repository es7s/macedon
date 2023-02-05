# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import time
from queue import Queue

import click
import psutil

from ._common import Options, Task, State, get_state
from .fileparser import get_parser
from .logger import get_logger
from .printer import get_printer
from .worker import Worker


class Synchronizer:
    def __init__(
        self,
        url_args: tuple[str],
        file: tuple[click.File],
    ):
        self._task_pool: Queue[Task] = Queue[Task]()
        self._workers: list[Worker] = []

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
        get_state().requests_latency.sort()
        printer.print_epilog(time_after - time_before)

    def _init_task_queue(self, url_args: tuple[str], file: tuple[click.File]):
        for file_inst in file:
            try:
                for task in get_parser().parse(file_inst):
                    self._append_task(task)
            except Exception as e:
                get_logger().error(f"Failed to parse the file '{file}': {e}")
        if get_state().requests_total.value > 0:
            return

        for url in url_args:
            if not url.startswith("http"):
                url = f"http://{url}"
            self._append_task(Task(url))

        if get_state().requests_total.value == 0:
            raise ValueError("No urls provided")

    def _append_task(self, task: Task):
        state = get_state()

        state.used_methods.add(task.method)
        for _ in range(state.options.amount):
            self._task_pool.put_nowait(task)
            state.requests_total.next()

    def _init_workers(self):
        state = get_state()
        threads = state.options.threads

        state.worker_states = ["init"] * threads
        for idx in range(threads):
            self._workers.append(Worker(self._task_pool, idx))


def get_default_thread_num() -> int:
    cores = psutil.cpu_count()
    if not cores:
        return 1
    if cores <= 4:
        return cores
    return min(16, cores // 2)
