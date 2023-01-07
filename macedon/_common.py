# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import queue
from dataclasses import dataclass, field
from threading import Lock

from requests.structures import CaseInsensitiveDict


class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock = Lock()

    def next(self) -> int:
        with self._lock:
            self._value += 1
            return self._value

    @property
    def value(self) -> int:
        return self._value


@dataclass(frozen=True)
class Options:
    color: bool
    threads: int
    amount: int
    delay: float
    timeout: float
    verbose: int
    show_id: bool
    show_error: bool


@dataclass(frozen=True)
class Task:
    url: str
    method: str = 'GET'
    headers: CaseInsensitiveDict = None
    body: str = None


@dataclass
class SharedState:
    last_request_id = ThreadSafeCounter()
    requests_total = ThreadSafeCounter()
    requests_printed = ThreadSafeCounter()
    requests_success = ThreadSafeCounter()
    requests_failed = ThreadSafeCounter()
    requests_latency: list[float] = field(default_factory=list)
    methods = set()
    worker_states: list[str] = None
