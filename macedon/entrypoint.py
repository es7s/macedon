import click


def invoke():
    callback()


@click.command
@click.pass_context
def callback(ctx: click.Context, **kwargs):
    print("entrypoint")
