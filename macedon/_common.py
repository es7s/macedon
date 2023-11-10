# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
from __future__ import annotations

import typing as t
from collections import deque
from dataclasses import dataclass, field
from threading import Event, Lock

import click
import psutil
import pytermor as pt
from requests.structures import CaseInsensitiveDict

_state: State | None = None


def get_state() -> State:
    if _state is None:
        raise Exception("State is not initialized")
    return _state


def init_state(options: Options):
    global _state
    _state = State(options)
    return _state


def destroy_state():
    global _state
    _state = None


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


@dataclass(frozen=True)
class State:
    options: Options
    last_request_id: ThreadSafeCounter = field(default_factory=ThreadSafeCounter)
    requests_total: ThreadSafeCounter = field(default_factory=ThreadSafeCounter)
    requests_printed: ThreadSafeCounter = field(default_factory=ThreadSafeCounter)
    requests_success: ThreadSafeCounter = field(default_factory=ThreadSafeCounter)
    requests_failed: ThreadSafeCounter = field(default_factory=ThreadSafeCounter)
    requests_latency: list[float] = field(default_factory=list)
    used_methods: set[str] = field(default_factory=set[str])
    worker_states: deque[str] = field(default_factory=deque[str])
    shutdown_flag: Event = field(default_factory=Event)


@dataclass(frozen=True)
class Options:
    endpoint_url: tuple[str]
    file: tuple[t.TextIO]
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


class FixedWidthStringWrapper(pt.StringReplacerChain):
    def __init__(self, width: int = 80):
        super().__init__(
            "(?s).+",
            pt.StringReplacer(R"\s+", " "),
            pt.StringReplacer(fR"(.{{{width}}})", r"\1\n"),
        )


class HiddenIntRange(click.IntRange):
    def _describe_range(self) -> str:
        return ""
