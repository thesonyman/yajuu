'''Yajuu is an automated media downloader.

Usage:
    yajuu media list <media>
    yajuu media download <media> <name>
    yajuu (-h | --help)
    yajuu --version
'''

import pkg_resources
from docopt import docopt


__version__ = pkg_resources.require('yajuu')[0].version


def main():
    arguments = docopt(__doc__)

    if arguments['--version']:
        print('Yajuu {}'.format(__version__))
    elif arguments['media']:
        if arguments['list']:
            print('Listing media {}'.format(arguments['<media>']))
        elif arguments['download']:
            print('Download media {}, the query is {}'.format(
                arguments['<media>'], arguments['<name>']
            ))
