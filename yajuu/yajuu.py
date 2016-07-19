import logging
import time
import pip

import click
import click_log

from yajuu.cli import download, plex
from yajuu.media import MEDIA_TYPES

# Use 'yajuu' instead of __name__, because since __name__ is 'yajuu.yajuu', the
# sub-packages won't be affected by the configuration.
logger = logging.getLogger('yajuu')


@click.group()
@click_log.simple_verbosity_option()
@click_log.init('yajuu')
def cli():
    # Mute the requests logger for the info level
    if logger.level >= logging.INFO:
        logging.getLogger('requests').setLevel(logging.WARNING)


@click.group()
@click.option(
    '--media-type', type=click.Choice(MEDIA_TYPES.keys()), default='anime'
)
@click.pass_context
def media(ctx, media_type):
    ctx.obj['START_TIME'] = time.time()
    ctx.obj['MEDIA_TYPE'] = media_type
    ctx.obj['MEDIA_CLASS'] = MEDIA_TYPES[media_type][0]
    ctx.obj['ORCHESTRATOR_CLASS'] = MEDIA_TYPES[media_type][1]


@click.command()
@click.option('--branch', default='master')
def upgrade(branch):
    pip.main([
        'install', '--upgrade',
        'git+https://github.com/vivescere/yajuu@{}'.format(branch)
    ])


@click.group()
def configure():
    pass

configure.add_command(plex)

media.add_command(download)

cli.add_command(media)
cli.add_command(configure)
cli.add_command(upgrade)


def main():
    cli(obj={})
