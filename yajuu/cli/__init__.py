import logging

import click
import click_log

from yajuu.cli.media import media
from yajuu.cli.configure import configure
from yajuu.cli.upgrade import upgrade
from yajuu.cli.dev import dev

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


cli.add_command(media)
cli.add_command(configure)
cli.add_command(upgrade)
cli.add_command(dev)
