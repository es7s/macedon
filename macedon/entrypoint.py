import click

from .options import Options
from .synchronizer import Synchronizer


def invoke():
    callback()


@click.command(no_args_is_help=True)
@click.argument("ENDPOINT_URL", type=str, nargs=-1)
@click.option(
    "-t",
    "--threads",
    type=int,
    default=1,
    show_default=True,
    help="numbers of threads for concurrent request making",
)
@click.pass_context
def callback(ctx: click.Context, endpoint_url: tuple[str], **kwargs):
    options = Options(**kwargs)
    Synchronizer(endpoint_url, options).run()
