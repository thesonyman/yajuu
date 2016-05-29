'''Provides an entry point for the media command.'''

import sys

VALID_MEDIAS = ('anime',)


def handle_media_cli(arguments):
    media = arguments['<media>'].lower()

    if media not in VALID_MEDIAS:
        print('The passed media is invalid, the correct ones are: {}.'.format(
            ', '.join(VALID_MEDIAS)
        ))

        sys.exit(1)

    if arguments['list']:
        _handle_media_list(media)
    elif arguments['download']:
        query = arguments['<name>']
        _handle_media_download(media, query)


def _handle_media_list(media):
    pass


def _handle_media_download(media, query):
    pass
