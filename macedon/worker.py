# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import json
import threading as t
import time
from collections.abc import Iterable
from queue import Queue, Empty
import pytermor as pt
import requests
import urllib3.exceptions
from requests import Response, JSONDecodeError
from requests.structures import CaseInsensitiveDict

from ._common import get_state, State, Task, FixedWidthStringWrapper
from .logger import get_logger
from .printer import get_printer


class Worker(t.Thread):
    def __init__(self, task_pool: Queue[Task], idx: int):
        self._state: State = get_state()
        self._task_pool: Queue[Task] = task_pool
        self._idx: int = idx
        super().__init__(target=self.run, name=f"#{idx}")

    def run(self):
        logger = get_logger()
        printer = get_printer()
        options = self._state.options

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

            delay = options.delay
            self._update_state("waiting")
            while delay > 0:
                if self._shutdown_on_flag():
                    return
                time.sleep(1)
                delay -= 1

            request_id = self._state.last_request_id.next()
            logger.info(f"Request #{request_id}: {task.method} {task.url}")

            response = None
            request_params = dict(
                headers=task.headers,
                data=task.body,
                allow_redirects=True,
                timeout=(options.timeout / 2, options.timeout / 2),
                verify=(not options.insecure and task.url.startswith("https")),
            )
            exception = None

            self._update_state("requesting")
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
                logger.info(f"Response #{request_id}: {self._get_status_code(response)}")
            else:
                self._state.requests_failed.next()
                printer.print_failed_request(task, time_after - time_before, request_id, exception)
                logger.info(f"No response for #{request_id}")
            self._trace_result(task, response, request_id)

    def _update_state(self, state: str):
        prev_state = self._state.worker_states[self._idx]
        get_logger().debug(" -> ".join(map(str.upper, [prev_state, state])))
        self._state.worker_states[self._idx] = state

    def _shutdown_on_flag(self) -> bool:
        if get_state().shutdown_flag.is_set():
            self._update_state("dead")
            return True
        return False

    def _get_status_code(self, response: Response) -> str:
        result = f"HTTP {response.status_code}"
        result += " " + response.reason
        return result

    def _trace_result(self, task: Task, response: Response, request_id: int):
        dump_parts = [
            "",
            f"# [R/R {request_id}]",
            *self._trace_request(task),
            *self._trace_response(response),
        ]
        get_logger().trace("\n".join(dump_parts))

    def _trace_request(self, task: Task):
        try:
            body = self._dump_json(json.loads(task.body))
        except (TypeError, json.decoder.JSONDecodeError):
            body = task.body

        yield from self._dump_combine(f"{task.method} {task.url}", ">", task.headers, body)

    def _trace_response(self, response: Response):
        try:
            body = self._dump_json(response.json())
        except AttributeError:
            yield from self._dump_combine("<no response>", "-")
            return  # response = None
        except JSONDecodeError:
            if response.encoding:
                if response.apparent_encoding:
                    response.encoding = response.apparent_encoding
                body = response.text
            else:
                binary_data_filters = [pt.OmniSanitizer, pt.OmniDecoder, FixedWidthStringWrapper]
                body = pt.apply_filters(response.content, *binary_data_filters)

        yield from self._dump_combine(self._get_status_code(response), "<", response.headers, body)

    def _dump_json(self, data: list | dict) -> str:
        return json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True)

    def _dump_combine(
        self,
        intro: str,
        mark: str,
        headers: CaseInsensitiveDict[str, str] = None,
        body: str = None,
    ) -> Iterable[str]:
        yield mark * 80
        yield mark + " " + intro
        if headers:
            yield from self._dump_headers(headers, mark)
            yield ""
        if body:
            yield body

    def _dump_headers(self, headers: CaseInsensitiveDict[str] | None, mark: str) -> Iterable[str]:
        for k, v in sorted(headers.items()):
            yield f"{mark} {k+':':s} {v}"
