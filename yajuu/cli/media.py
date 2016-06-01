'''Provides an entry point for the media command.'''

import sys
import tabulate

from yajuu.media import Anime

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
        # The tuple contains the query and the season(s) as a list.

        queries = list((x, None) for x in arguments['<names>'])

        if arguments['--seasons']:
            season_args = (
                x.strip() for x in arguments['--seasons'].split(',')
            )

            for index, season_arg in enumerate(season_args):
                try:
                    season_arg = int(season_arg)

                    if 0 <= index < len(queries):
                        queries[index] = (queries[index][0], season_arg)
                except (ValueError, TypeError):
                    pass

        _handle_media_download(media, queries)


def _handle_media_list(media):
    pass


def _handle_media_download(media, queries):
    # Get the animes
    print('Getting the needed metadata...')

    animes = []

    for query, season in queries:
        try:
            anime = Anime(query)

            if season is not None:
                if season not in anime.get_seasons():
                    message = (
                        'warning: the season n°{} was not found for the anime'
                        '"{}" (has {} seasons).'
                    )

                    print(message.format(
                        season, anime.metadata['name'],
                        len(anime.get_seasons()) - 1
                    ))

                    season = []
                else:
                    season = [season]
            else:
                season = list(anime.get_seasons())

            if len(season) > 0:
                animes.append((anime, season))
        except Anime.MediaNotFoundException as e:
            print('The specified anime could not be found.')
            sys.exit(1)

    # Print the summary before starting
    print('\nAnimes to download now: ')

    print(tabulate.tabulate(
        ((
            anime.metadata['name'],
            ', '.join(str(x) for x in season)
        ) for anime, season in animes),
        headers=('Name', 'Season(s)'), tablefmt='psql'
    ))

    print('\n')

    # Get confirmation from the user to start
    choice = None

    while choice is None:
        try:
            user_input = input(':: Proceed with downloading? [Y/n] ').lower()
        except KeyboardInterrupt:
            choice = False
            continue

        if user_input == '' or user_input == 'y':
            choice = True
        elif user_input == 'n':
            choice = False

    if not choice:
        sys.exit(0)

    print('\n:: Preparing the extractors')
