# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import os
import signal
import sys

import click
import urllib3
from urllib3.exceptions import InsecureRequestWarning

import pytermor as pt
from . import APP_NAME, APP_VERSION
from ._common import Options, init_state, get_state
from .fileparser import init_parser
from .io import init_io
from .logger import init_loggers, get_logger
from .printer import init_printer, get_printer
from .synchronizer import Synchronizer, get_default_thread_num

_shutdown_started = False


def invoke():
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    callback()


def shutdown():
    global _shutdown_started
    _shutdown_started = True
    get_state().shutdown_flag.set()
    get_printer().print_shutdown()

def exit_gracefully(signal_code: int, *args):
    get_logger().debug(f"{signal.Signals(signal_code).name} ({signal_code}) received")
    if not _shutdown_started:
        shutdown()
        return
    os._exit(0)


class ClickCommand(click.Command):
    pass


@click.command(
    cls=ClickCommand,
    no_args_is_help=True,
    context_settings=dict(max_content_width=pt.get_preferable_wrap_width()),
)
@click.argument("ENDPOINT_URL", type=str, nargs=-1)
@click.option(
    "-T",
    "--threads",
    type=int,
    default=get_default_thread_num(),
    show_default=True,
    help="Number of threads for concurrent request making. Default value depends "
         "on number of CPU cores available in the system.",
)
@click.option(
    "-n",
    "--amount",
    type=int,
    default=1,
    show_default=True,
    help="How many times each request will be performed.",
)
@click.option(
    "-d",
    "--delay",
    type=float,
    default=0,
    show_default=True,
    help="Seconds to wait between requests.",
)
@click.option(
    "-t",
    "--timeout",
    type=float,
    default=10,
    show_default=True,
    help="Seconds to wait for the response.",
)
@click.option(
    "-f",
    "--file",
    multiple=True,
    type=click.types.File(),
    help="Execute request(s) from a specified file. The file should contain a list of "
    "endpoints in the format '{method} {url}', one per line. Another supported "
    "(partially) format is JetBrains HTTP Client format, which additionally allows to "
    "specify request headers and body. The option can be specified multiple times. "
    "The ENDPOINT_URL argument(s) are ignored if this option is present.",
)
@click.option(
    "-c/-C",
    "--color/--no-color",
    is_flag=True,
    default=None,
    help="",
)
@click.option(
    "--show-id",
    is_flag=True,
    help="",
)
@click.option(
    "--show-error",
    is_flag=True,
    help="",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    type=click.types.IntRange(min=0, max=3, clamp=True),
    default=0,
    help="Increase details level: -v for request info, -vv for debugging worker "
         "threads debugging, -vvv for response tracing",
)
def callback(endpoint_url: tuple[str], file: tuple[click.File], **kwargs):
    options = Options(**kwargs)
    urllib3.disable_warnings(InsecureRequestWarning)

    init_state(options)
    init_io(options)
    init_loggers(options)
    _log_init_info(options)

    init_parser()
    init_printer()
    sync = Synchronizer(endpoint_url, file)
    sync.run()


def _log_init_info(options: Options):
    logger = get_logger()
    logger.debug(
        f"{APP_NAME} {APP_VERSION} "
        f"PID={os.getpid()} PPID={os.getppid()} "
        f"UID={os.getuid()} CWD={os.getcwd()}"
    )
    logger.debug(f"Args: {sys.argv!r}")
    logger.debug(f"Options: {options!r}")
