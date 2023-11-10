# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import logging
import sys
from logging import (
    Formatter as BaseFormatter,
    LogRecord as BaseLogRecord,
    Logger as BaseLogger,
    StreamHandler,
    getLogger,
)
import pytermor as pt
from ._common import Options
from .io import get_stderr

TRACE = 15

VERBOSITY_LOG_LEVELS = {
    0: logging.CRITICAL,
    1: logging.INFO,
    2: TRACE,
    3: logging.DEBUG,
}


class Logger(BaseLogger):
    def trace(self, msg: str, *args, **kwargs):
        self.log(level=TRACE, msg=msg, *args, **kwargs)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
        if level > logging.INFO:
            # for any warning/error/critical:
            if exc_info:
                # show stack traces if verbosity>=2 (-vv), except ...
                exc_info = self.level <= TRACE
            else:
                # ... when exc_info was manually disabled (requests' errors),
                # in which case show traces only at max level verbosity (-vvv)
                exc_info = self.level <= logging.DEBUG
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)  # noqa


_logger: Logger | None = None


def get_logger() -> Logger:
    if _logger is None:
        raise Exception("Logger should be initialized")
    return _logger


def init_logger(options: Options) -> Logger:
    logging.addLevelName(TRACE, "TRACE")
    logging.setLoggerClass(Logger)
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
    return _logger


def destroy_logger():
    global _logger
    _logger = None


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
        super().__init__(name, level, pathname, lineno, msg, args, exc_info, func, sinfo)
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
    # fmt: off
    LEVEL_TO_FMT_MAP: dict[int, pt.FT] = {
        logging.DEBUG:      pt.Style(fg=pt.Color256.get_by_code(66)),
        TRACE:              pt.Style(fg=pt.Color256.get_by_code(60)),
        logging.INFO:       pt.cv.WHITE,
        logging.WARNING:    pt.cv.YELLOW,
        logging.ERROR:      pt.cv.RED,
        logging.CRITICAL:   pt.cv.HI_RED,
    }
    # fmt: on

    def __init__(self, options: Options):
        ts = self._get_rel_time_tpl(options)
        fmt = f"[%(levelname)-5.5s][%(name)s:%(threadName)s]{ts} %(message)s"
        super(SgrFormatter, self).__init__(fmt)

    def format(self, record: LogRecord) -> str:
        result = super().format(record)
        fmt = self.LEVEL_TO_FMT_MAP.get(record.levelno, pt.NOOP_STYLE)
        return get_stderr().render(result, fmt)
