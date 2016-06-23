import click

from .cli import download
from .media import Anime

MEDIA_TYPES = {
    'anime': Anime
}


@click.group()
@click.option(
    '--media-type', type=click.Choice(MEDIA_TYPES.keys()), default='anime'
)
@click.pass_context
def cli(ctx, media_type):
    ctx.obj['MEDIA_TYPE'] = MEDIA_TYPES[media_type]

cli.add_command(download)


def main():
    cli(obj={})
