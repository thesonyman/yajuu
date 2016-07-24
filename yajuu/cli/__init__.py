'''Definition of lazy loading commands. Since each command can take a long time
to load, we wrap them and load them only when the user really calls them.
We can save ~700 ms, which is a lot.'''

import click
from yajuu.cli.media.download.download_parser import validate_media


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


@click.command()
@click.option(
    '--only-print', is_flag=True,
    help='Only print the configuration as yaml, does not save it.'
)
def plex(*args, **kwargs):
    from yajuu.cli.configure.plex import plex as _plex
    _plex(*args, **kwargs)
