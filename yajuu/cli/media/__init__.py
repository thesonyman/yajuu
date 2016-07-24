import time

import click

from yajuu.types import MEDIA_TYPES_KEYS
from yajuu.cli.media.download.download_parser import validate_media


@click.group()
@click.option(
    '--media-type', type=click.Choice(MEDIA_TYPES_KEYS), default='anime'
)
@click.pass_context
def media(ctx, media_type):
    from yajuu.media.types import MEDIA_TYPES

    ctx.obj['START_TIME'] = time.time()
    ctx.obj['MEDIA_TYPE'] = media_type
    ctx.obj['MEDIA_CLASS'] = MEDIA_TYPES[media_type][0]
    ctx.obj['ORCHESTRATOR_CLASS'] = MEDIA_TYPES[media_type][1]


@click.command()
@click.pass_context
@click.option(
    '-m', '--media', callback=validate_media, multiple=True, required=True,
    help='Add a media to download, the string must respect the format "Name '
    'season[s] s,..". Eg: "Code Geass" seasons 1,2. The option can be passed '
    'multiple times.'
)
@click.option(
    '--skip-confirmation', is_flag=True, help='Skip the first confirmation, '
    'however you will still need to select the correct results'
)
@click.option(
    '--automatic', is_flag=True,
    help='Skip all the websites that does not have a perfect match. This '
    'reduce the number of sources drastically.'
)
@click.option(
    '--dump', is_flag=True,
    help='Skip the integrated download phase and instead dumps all the links '
    'to multiple text file.'
)
def download(*args, **kwargs):
    from yajuu.cli.media.download.download import download as _download
    _download(*args, **kwargs)


media.add_command(download)
