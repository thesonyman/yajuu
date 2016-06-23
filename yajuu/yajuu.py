import logging

import click
import click_log

from .cli import download
from .media import Anime
from .extractors import AnimeOrchestrator

# Use 'yajuu' instead of __name__, because since __name__ is 'yajuu.yajuu', the
# sub-packages won't be affected by the configuration.
logger = logging.getLogger('yajuu')

MEDIA_TYPES = {
    'anime': (Anime, AnimeOrchestrator)
}


@click.group()
@click.option(
    '--media-type', type=click.Choice(MEDIA_TYPES.keys()), default='anime'
)
@click_log.simple_verbosity_option()
@click_log.init('yajuu')
@click.pass_context
def cli(ctx, media_type):
    ctx.obj['MEDIA_CLASS'] = MEDIA_TYPES[media_type][0]
    ctx.obj['ORCHESTRATOR_CLASS'] = MEDIA_TYPES[media_type][1]

cli.add_command(download)


def main():
    cli(obj={})
