# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import logging
import sys

from ._common import Options

VERBOSITY_LOG_LEVELS = {
    0: logging.CRITICAL,
    1: logging.INFO,
    2: logging.DEBUG,
}


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
    _handler.setFormatter(logging.Formatter("[%(levelname)-5.5s][%(name)s:%(threadName)s] %(message)s"))
    _handler.setLevel(log_level)
    _logger.addHandler(_handler)
    _logger.setLevel(log_level)

    pt_logger = logging.getLogger("pytermor")
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "[%(levelname)-5.5s][%(name)s|%(module)s] %(message)s")
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    pt_logger.addHandler(handler)
    pt_logger.setLevel(log_level)

    return _logger


_logger: logging.Logger|None = None
