# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
from __future__ import annotations
from threading import Lock, Event
from dataclasses import dataclass, field

import psutil
from requests.structures import CaseInsensitiveDict


_state: State|None = None


def get_state() -> State:
    if _state is None:
        raise Exception("State is not initialized")
    return _state


def init_state(options: Options):
    global _state
    _state = State(options)
    return _state


def get_default_thread_num() -> int:
    cores = psutil.cpu_count()
    if not cores:
        return 1
    if cores <= 4:
        return cores
    return min(16, cores // 2)


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


@dataclass
class State:
    options: Options
    last_request_id = ThreadSafeCounter()
    requests_total = ThreadSafeCounter()
    requests_printed = ThreadSafeCounter()
    requests_success = ThreadSafeCounter()
    requests_failed = ThreadSafeCounter()
    requests_latency: list[float] = field(default_factory=list)
    used_methods: set[str] = field(default_factory=set[str])
    worker_states: list[str] = None
    shutdown_flag: Event = Event()


@dataclass(frozen=True)
class Options:
    amount: int = 1
    color: bool = None
    delay: float = 0
    insecure: bool = False
    exit_code: bool = False
    show_error: bool = False
    show_id: bool = False
    threads: int = get_default_thread_num()
    timeout: float = 10
    verbose: int = 0


@dataclass(frozen=True)
class Task:
    url: str
    method: str = "GET"
    headers: CaseInsensitiveDict = None
    body: str = None
