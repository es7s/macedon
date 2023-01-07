# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import os
import sys

import click
import pytermor as pt
import urllib3
from click import Context, HelpFormatter
from urllib3.exceptions import InsecureRequestWarning

from . import APP_NAME, APP_VERSION
from ._common import Options, SharedState
from .fileparser import init_parser
from .io import init_io
from .logger import init_loggers, get_logger
from .printer import init_printer
from .synchronizer import Synchronizer


def invoke():
    callback()


class ClickCommand(click.Command):
    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        pieces = self.collect_usage_pieces(ctx)
        formatter.write_usage(ctx.command_path, "|".join(pieces))


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
    default=1,
    show_default=True,
    help="Number of threads for concurrent request making.",
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
    help="Seconds to wait between each request.",
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
    type=click.types.IntRange(min=0, max=2, clamp=True),
    default=0,
    help="Display detailed info on every request.",
)
@click.pass_context
def callback(
    ctx: click.Context, endpoint_url: tuple[str], file: tuple[click.File], **kwargs
):
    options = Options(**kwargs)
    shared_state = SharedState()
    urllib3.disable_warnings(InsecureRequestWarning)

    init_io(options)
    init_loggers(options)
    _log_init_info(options)

    init_parser()
    init_printer(options, shared_state)
    sync = Synchronizer(endpoint_url, file, options, shared_state)
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
