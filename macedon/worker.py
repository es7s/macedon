# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import threading as t
import time
from queue import Queue, Empty

import pytermor as pt
import requests
import urllib3.exceptions
from requests import Response

from ._common import Options, Task, SharedState
from .logger import get_logger
from .printer import get_printer


class Worker(t.Thread):
    def __init__(
        self,
        options: Options,
        task_pool: Queue[Task],
        idx: int,
        shared_state: SharedState,
    ):
        self._options = options
        self._task_pool = task_pool
        self._idx = idx
        self._shared_state = shared_state
        super().__init__(target=self.run, name=f"#{idx}")

    def run(self):
        logger = get_logger()
        printer = get_printer()

        while True:
            try:
                task = self._task_pool.get_nowait()
            except Empty:
                logger.debug(f"Empty queue, terminating")
                self._update_state("dead")
                return
            if not task:
                continue
            if (delay := self._options.delay) > 0:
                self._update_state("sleep")
                time.sleep(delay)

            response = None
            request_id = self._shared_state.last_request_id.next()
            request_params = dict(
                headers=task.headers,
                data=task.body,
                allow_redirects=True,
                timeout=self._options.timeout,
                verify=task.url.startswith("https"),
            )
            logger.info(
                f"Performing request #{request_id}: {task.method} {task.url} {request_params}"
            )
            exception = None
            self._update_state("request")
            time_before = time_after = time.time_ns()
            try:
                response = requests.request(task.method, task.url, **request_params)
            except urllib3.exceptions.InsecureRequestWarning as e:
                logger.warning(e)
            except requests.exceptions.RequestException as e:
                time_after = time.time_ns()
                logger.exception(e, exc_info=False)
                exception = e

            if response is not None:
                if response.ok:
                    self._shared_state.requests_success.next()
                else:
                    self._shared_state.requests_failed.next()

                self._shared_state.requests_latency.append(response.elapsed.total_seconds())
                printer.print_response(task, response, request_id)
                self._dump_response(response, request_id)
            else:
                self._shared_state.requests_failed.next()
                printer.print_failed_request(task, time_after - time_before, request_id, exception)
                logger.info(f"No response for #{request_id}")

    def _update_state(self, state: str):
        get_logger().debug(f"State -> {state}")
        self._shared_state.worker_states[self._idx] = state

    def _dump_response(self, response: Response, request_id: int):
        logger = get_logger()
        logger.info(
            f"Response #{request_id} metadata: {response.status_code} {response.headers}"
        )
        try:
            logger.debug(
                pt.dump(response.content.decode(), f"Response #{request_id} content")
            )
        except UnicodeError:
            logger.debug(
                pt.BytesTracer().apply(
                    response.content,
                    pt.TracerExtra(f"Response #{request_id} raw content"),
                )
            )
