# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import logging
from logging import (
    LogRecord as BaseLogRecord,
    Formatter as BaseFormatter,
    StreamHandler,
    getLogger,
    Logger,
    Manager,
)
import sys
from typing import Mapping, Any

import pytermor as pt
from ._common import Options
from .io import get_stderr

TRACE = 5


VERBOSITY_LOG_LEVELS = {
    0: logging.CRITICAL,
    1: logging.INFO,
    2: logging.DEBUG,
    3: TRACE,
}


_logger: Logger | None = None


def get_logger() -> Logger:
    if _logger is None:
        raise Exception("Logger should be initialized")
    return _logger


def init_loggers(options: Options):
    logging.addLevelName(TRACE, "TRACE")
    logging.setLogRecordFactory(LogRecord)

    log_level = VERBOSITY_LOG_LEVELS.get(options.verbose, logging.WARNING)

    if options.verbose >= 2:
        getLogger().setLevel(log_level)  # root logger

    from . import APP_NAME

    global _logger
    _logger = getLogger(APP_NAME)
    _handler = StreamHandler(sys.stderr)
    _handler.setFormatter(SgrFormatter(options))
    _handler.setLevel(log_level)
    _logger.addHandler(_handler)
    _logger.setLevel(log_level)

    pt_logger = getLogger("pytermor")
    handler = StreamHandler(sys.stderr)
    handler.setFormatter(PytermorFormatter(options))
    handler.setLevel(log_level)
    pt_logger.addHandler(handler)
    pt_logger.setLevel(log_level)

    return _logger


class LogRecord(BaseLogRecord):
    def __init__(
        self,
        name: str,
        level: int,
        pathname: str,
        lineno: int,
        msg: object,
        args,
        exc_info,
        func: str | None = ...,
        sinfo: str | None = ...,
    ) -> None:
        super().__init__(
            name, level, pathname, lineno, msg, args, exc_info, func, sinfo
        )
        self.rel_created_str = pt.format_time_delta(self.relativeCreated / 1000, 6)


class Formatter(BaseFormatter):
    def _get_rel_time_tpl(self, options: Options) -> str:
        if options.verbose >= 2:
            return "(+%(rel_created_str)s)"
        return ""


class PytermorFormatter(Formatter):
    def __init__(self, options: Options):
        ts = self._get_rel_time_tpl(options)
        fmt = f"[%(levelname)-5.5s][%(name)s|%(module)s]{ts} %(message)s"
        super(PytermorFormatter, self).__init__(fmt)


class SgrFormatter(Formatter):
    LEVEL_TO_FMT_MAP: dict[int, pt.FT] = {
        TRACE:         pt.Style(fg=pt.Color256.get_by_code(60)),
        logging.DEBUG: pt.Style(fg=pt.Color256.get_by_code(66)),
        logging.INFO: pt.cv.WHITE,
        logging.WARNING: pt.cv.YELLOW,
        logging.ERROR: pt.cv.RED,
        logging.CRITICAL: pt.cv.HI_RED,
    }

    def __init__(self, options: Options):
        ts = self._get_rel_time_tpl(options)
        fmt = f"[%(levelname)-5.5s][%(name)s:%(threadName)s]{ts} %(message)s"
        super(SgrFormatter, self).__init__(fmt)

    def format(self, record: LogRecord) -> str:
        result = super().format(record)
        fmt = self.LEVEL_TO_FMT_MAP.get(record.levelno, pt.NOOP_STYLE)
        return get_stderr().render(result, fmt)
