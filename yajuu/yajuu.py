'''Yajuu is an automated media downloader.

Usage:
    yajuu media list <media>
    yajuu media download <media> <name>
    yajuu (-h | --help)
    yajuu --version
'''

import pkg_resources
from docopt import docopt

from .cli import handle_media_cli


__version__ = pkg_resources.require('yajuu')[0].version


def main():
    ensure_config_directory()
    handle_cli()


def handle_cli():
    """Will call submodules in the cli package if needed."""

    arguments = docopt(__doc__)

    if arguments['--version']:
        print('Yajuu {}'.format(__version__))
    elif arguments['media']:
        handle_media_cli(arguments)


def ensure_config_directory():
    pass
