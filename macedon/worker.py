# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import threading as t
import time
from queue import Queue, Empty

import requests
import urllib3.exceptions
from requests import Response

import pytermor as pt
from ._common import Options, Task, get_state, State
from .logger import get_logger, TRACE
from .printer import get_printer


class Worker(t.Thread):
    def __init__(
        self,
        task_pool: Queue[Task],
        idx: int,
    ):
        self._state: State = get_state()
        self._task_pool: Queue[Task] = task_pool
        self._idx: int = idx
        super().__init__(target=self.run, name=f"#{idx}")

    def run(self):
        logger = get_logger()
        printer = get_printer()

        while True:
            if self._shutdown_on_flag():
                return
            try:
                task = self._task_pool.get_nowait()
            except Empty:
                logger.debug(f"Empty queue, terminating")
                self._update_state("dead")
                return
            if not task:
                continue

            delay = self._state.options.delay
            self._update_state("sleep")
            while delay > 0:
                if self._shutdown_on_flag():
                    return
                time.sleep(1)
                delay -= 1

            response = None
            request_id = self._state.last_request_id.next()
            request_params = dict(
                headers=task.headers,
                data=task.body,
                allow_redirects=True,
                timeout=(self._state.options.timeout/2, self._state.options.timeout/2),
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
                    self._state.requests_success.next()
                else:
                    self._state.requests_failed.next()

                self._state.requests_latency.append(response.elapsed.total_seconds())
                printer.print_completed_request(task, response, request_id)
                self._dump_response(response, request_id)
            else:
                self._state.requests_failed.next()
                printer.print_failed_request(
                    task, time_after - time_before, request_id, exception
                )
                logger.info(f"No response for #{request_id}")

    def _update_state(self, state: str):
        get_logger().debug(f"State -> {state}")
        self._state.worker_states[self._idx] = state

    def _shutdown_on_flag(self) -> bool:
        if get_state().shutdown_flag.is_set():
            self._update_state("dead")
            return True
        return False

    def _dump_response(self, response: Response, request_id: int):
        label = f"Response #{request_id} %s:"
        info_parts = [label % "metadata", str(response.status_code), str(response.headers)]

        logger = get_logger()
        logger.info(" ".join(info_parts))
        try:
            decoded = response.content.decode()
            logger.log(TRACE, pt.dump(decoded, label % "content"))
        except UnicodeError:
            trace = pt.BytesTracer().apply(
                response.content,
                pt.TracerExtra(label % "raw content"),
            )
            logger.log(TRACE, trace)
