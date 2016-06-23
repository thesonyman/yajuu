'''Yajuu is an automated media downloader.

Usage:
    yajuu media list <media>
    yajuu media repair <media>
    yajuu media download <media> (<names> ...) [--seasons=<seasons>]
    yajuu (-h | --help)
    yajuu --version

Options:
    -s, --seasons=<seasons> String that tell which seasons to download.
                            Separate the medias using comas. For 'A', 'B' you
                            could pass -s '1, 1'. Pass -1 to target all the
                            seasons.
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
