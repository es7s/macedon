# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
import os
import signal
import sys

import click
import es7s_commons
import urllib3
from click import pass_context
from es7s_commons import format_path, format_attrs
from urllib3.exceptions import InsecureRequestWarning

import pytermor as pt
from . import APP_NAME, APP_VERSION, APP_UPDATED
from ._common import Options, destroy_state, init_state, get_state, HiddenIntRange
from .fileparser import destroy_parser, init_parser
from .io import destroy_io, init_io
from .logger import destroy_logger, init_logger, get_logger
from .printer import destroy_printer, init_printer, get_printer
from .synchronizer import Synchronizer

_shutdown_started = False


def invoke():
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    try:
        callback()
    except Exception as e:
        print(f"Error: {e}")


def shutdown():
    global _shutdown_started
    _shutdown_started = True
    get_state().shutdown_flag.set()
    get_printer().print_shutdown()


def exit_gracefully(signal_code: int, *args):
    get_logger().info(f"{signal.Signals(signal_code).name} ({signal_code}) received")
    if not _shutdown_started:
        shutdown()
        return
    os._exit(0)  # noqa


class ClickCommand(click.Command):
    pass


@click.command(
    cls=ClickCommand,
    no_args_is_help=True,
    context_settings=dict(max_content_width=pt.get_preferable_wrap_width()),
    epilog="""JetBrains HTTP Client format is described here: 
\b

    https://jetbrains.com/help/idea/exploring-http-syntax.html""",
)
@click.argument("ENDPOINT_URL", type=str, nargs=-1)
@click.option(
    "-T",
    "--threads",
    type=int,
    default=Options.threads,
    show_default=True,
    help="Number of threads for concurrent request making. Default value depends "
    "on number of CPU cores available in the system.",
)
@click.option(
    "-n",
    "--amount",
    type=int,
    default=Options.amount,
    show_default=True,
    help="How many times each request will be performed.",
)
@click.option(
    "-d",
    "--delay",
    type=float,
    default=Options.delay,
    show_default=True,
    help="Seconds to wait between requests.",
)
@click.option(
    "-t",
    "--timeout",
    type=float,
    default=Options.timeout,
    show_default=True,
    help="Seconds to wait for the response.",
)
@click.option(
    "-i",
    "--insecure",
    is_flag=True,
    default=Options.insecure,
    help="Ignore invalid/expired certificates when performing HTTPS requests.",
)
@click.option(
    "-f",
    "--file",
    multiple=True,
    type=click.types.File(),
    help="Execute request(s) from a specified file, or from stdin, if FILENAME "
    "specified as '-'. The file should contain a list of endpoints in the format "
    "'{method} {url}', one per line. Another (partially) supported format is "
    "JetBrains HTTP Client format (see below), which additionally allows to "
    "specify request headers and/or body. The option can be specified multiple times. "
    "Note that ENDPOINT_URL argument(s) are ignored if this option is present.",
)
@click.option(
    "-x",
    "--exit-code",
    is_flag=True,
    default=Options.exit_code,
    help="Return different exit codes depending on completed / failed requests. "
    "With this option exit code 0 is returned if and only if each request was "
    "considered successful (1xx, 2xx HTTP codes); even one failed request (4xx, "
    "timed out, etc) will result in a non-zero exit code. (Normally the exit code "
    "0 is returned as long as the application terminated under normal conditions,"
    " regardless of an actual HTTP codes; but it can still die with a non-zero "
    "code upon invalid option syntax, etc).",
)
@click.option(
    "-c/-C",
    "--color/--no-color",
    is_flag=True,
    default=Options.color,
    help="Force output colorizing using ANSI escape sequences or disable it "
    "unconditionally. If omitted, the application determines it automatically "
    "by checking if the output device is a terminal emulator with SGR support.",
)
@click.option(
    "--show-id",
    is_flag=True,
    default=Options.show_id,
    help="Print a column with request serial number.",
)
@click.option(
    "--show-error",
    is_flag=True,
    default=Options.show_error,
    help="Print a column with network (not HTTP) error messages, when applicable.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    type=HiddenIntRange(min=0, max=3, clamp=True),
    default=Options.verbose,
    help="""\b
         Increase verbosity:
             -v for request details and exceptions;
            -vv for request/response contents and stack traces;
           -vvv for thread state transition messages.""",
)
@click.option(
    "--version",
    "-V",
    "mode_version",
    count=True,
    is_eager=True,
    help="Show the version and exit.",
)
def callback(mode_version: bool, **kwargs):
    if mode_version:
        invoke_version(value=mode_version, **kwargs)
        return

    options = Options(**kwargs)
    _init(options)

    sync = Synchronizer(options)
    sync.run()

    _destroy(options)


@pass_context
def invoke_version(ctx: click.Context, value: int, **kwargs):
    if not value or ctx.resilient_parsing:
        return
    vfmt = lambda s: pt.Fragment(s, "green")
    ufmt = lambda s: pt.Fragment(s, "gray")

    pt.echo(f"{APP_NAME:>12s}  {vfmt(APP_VERSION):<14s}  {ufmt(APP_UPDATED)}")
    pt.echo(f"{'pytermor':>12s}  {vfmt(pt.__version__):<14s}  {ufmt(pt.__updated__)}")
    pt.echo(
        f"{'es7s-commons':>12s}  {vfmt(es7s_commons.PKG_VERSION):<14s}  {ufmt(es7s_commons.PKG_UPDATED)}"
    )

    def _echo_path(label: str, path: str):
        pt.echo(
            pt.Composite(
                pt.Text(label + ":", width=17),
                format_path(path, color=True, repr=False),
            )
        )

    if value > 1:
        pt.echo()
        _echo_path("Executable", sys.executable)
        _echo_path("Entrypoint", __file__)
    ctx.exit()


def _init(options: Options):
    urllib3.disable_warnings(InsecureRequestWarning)

    init_state(options)
    init_io(options)
    init_logger(options)
    _log_init_info(options)

    init_parser()
    init_printer()


def _destroy(options: Options):
    exit_code = 0
    if options.exit_code:
        if get_state().requests_failed.value > 0:
            exit_code = 1

    destroy_state()
    destroy_printer()
    destroy_parser()
    destroy_logger()
    destroy_io()

    if exit_code:
        exit(exit_code)


def _log_init_info(options: Options):
    logger = get_logger()
    logger.info(
        f"{APP_NAME} {APP_VERSION} "
        + format_attrs(dict(PID=os.getpid(), PPID=os.getppid(), UID=os.getuid(), CWD=os.getcwd()))
    )
    logger.debug(f"Args: {format_attrs(sys.argv)}")
    logger.debug(repr(options))
