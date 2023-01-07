# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import logging
import os
import sys
from logging import LogRecord
from os import P_PID

import pytermor as pt

from ._common import Options
from .io import get_stderr

VERBOSITY_LOG_LEVELS = {
    0: logging.CRITICAL,
    1: logging.INFO,
    2: logging.DEBUG,
}


class SgrFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        result = super().format(record)
        fmt = pt.NOOP_STYLE
        match record.levelno:
            case logging.DEBUG:
                fmt = pt.cv.CYAN
            case logging.INFO:
                fmt = pt.cv.WHITE
            case logging.WARNING:
                fmt = pt.cv.YELLOW
            case logging.ERROR:
                fmt = pt.cv.RED
        return get_stderr().render(result, fmt)


def get_logger():
    return _logger


def init_loggers(options: Options):
    log_level = VERBOSITY_LOG_LEVELS.get(options.verbose, logging.WARNING)

    if options.verbose >= 2:
        logging.getLogger().setLevel(log_level)  # root logger

    from . import APP_NAME

    global _logger
    _logger = logging.getLogger(APP_NAME)
    _handler = logging.StreamHandler(sys.stderr)
    _handler.setFormatter(
        SgrFormatter("[%(levelname)-5.5s][%(name)s:%(threadName)s] %(message)s")
    )
    _handler.setLevel(log_level)
    _logger.addHandler(_handler)
    _logger.setLevel(log_level)

    pt_logger = logging.getLogger("pytermor")
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "[%(levelname)-5.5s][%(name)s|%(module)s] %(message)s"
    )
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    pt_logger.addHandler(handler)
    pt_logger.setLevel(log_level)

    return _logger


_logger: logging.Logger | None = None
