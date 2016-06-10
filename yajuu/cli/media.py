'''Provides an entry point for the media command.'''

import os
import sys
import shlex
import urllib.parse
import glob
from xml.dom import minidom

import tabulate
import requests

from yajuu.media import Anime
from yajuu.config import config
from .utils import confirm
from yajuu.extractors.anime.anime_orchestrator import AnimeOrchestrator
from yajuu.extractors.anime.htvanime import HtvanimeExtractor
from yajuu.extractors.anime.anime_haven import AnimeHavenExtractor
from yajuu.extractors.anime.anime_chiby import AnimeChibyExtractor

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
            season_args = list(
                x.strip().split(',') for x in arguments['--seasons'].split(';')
            )

            for index, seasons in enumerate(season_args):
                if not (0 <= index < len(queries)):
                    continue

                # Filter out the seasons that are not castable to an int
                good_seasons = []

                for season in seasons:
                    try:
                        season = int(season)
                        good_seasons.append(season)
                    except ValueError:
                        pass

                queries[index] = (queries[index][0], good_seasons)

        _handle_media_download(media, queries)


def _handle_media_list(media):
    pass


def _handle_media_download(media, queries):
    # Get the animes
    print('Getting the needed metadata...')

    animes = []

    for query, seasons in queries:
        for season in seasons:
            try:
                anime = Anime(query)

                if season is not None:
                    if season not in anime.get_seasons():
                        message = (
                            'warning: the season n°{} was not found for the '
                            'anime "{}" (has {} seasons).'
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
                    found = False

                    for index, _data in enumerate(animes):
                        if _data[0] == anime:
                            found = True

                            # Combine the seasons, keep the unique values and
                            # sort them.
                            season = list(set(_data[1] + season))
                            animes[index] = (anime, season)

                    if not found:
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
    choice = confirm('Is the above information correct?')

    if not choice:
        sys.exit(0)

    print('\n:: Preparing the extractors (please stay there)\n')

    orchestrators = []

    for anime, season in animes:
        orchestrator = AnimeOrchestrator(
            [HtvanimeExtractor, AnimeChibyExtractor, AnimeHavenExtractor],
            anime, season
        )

        orchestrator.search()

        orchestrators.append(orchestrator)

    min_quality = config['media']['minimum_quality']
    max_quality = config['media']['maximum_quality']
    preferred_quality = config['media']['preferred_quality']

    def filter_quality(source):
        quality = source[0]

        if quality < min_quality:
            return False
        elif max_quality > 0 and quality > max_quality:
            return False

        return True

    for orchestrator in orchestrators:
        sources = orchestrator.extract()

        print('\n:: Downloading anime "{}"'.format(
            orchestrator.media.metadata['name']
        ))

        base_path = os.path.join(
            config['paths']['base'],
            config['paths']['medias']['anime']['base'],
            orchestrator.media.metadata['name']
        )

        if not os.path.exists(base_path):
            os.makedirs(base_path)

        for season, episodes_sources in sources.items():
            print('=> Season {0:02d}'.format(season))

            season_path = os.path.join(
                base_path,
                config['paths']['medias']['anime']['season'].format(
                    season_number=season
                )
            )

            if not os.path.exists(season_path):
                os.makedirs(season_path)

            for episode_number, episode_sources in episodes_sources.items():
                episode_sources = list(filter(
                    filter_quality,
                    episode_sources
                ))

                if len(episode_sources) <= 0:
                    print(episode_number, ':: None')
                    continue

                if preferred_quality in map(lambda x: x[0], episode_sources):
                    for quality, url in episode_sources:
                        if quality == preferred_quality:
                            source = (quality, url)
                            break
                else:
                    source = max(episode_sources, key=lambda x: x[0])

                path = urllib.parse.urlparse(source[1]).path
                ext = os.path.splitext(path)[1][1:]

                if ext == '':
                    ext = 'mp4'

                episode_name = (
                    config['paths']['medias']['anime']['episode'].format(
                        anime_name=orchestrator.media.metadata['name'],
                        season_number=season, episode_number=episode_number,
                        ext='{}'
                    )
                )

                episode_path = os.path.join(season_path, episode_name)

                # Try to find out if the file already exists
                exists = len(glob.glob(
                    episode_path.format('*')  # Replace ext with *
                )) > 0

                if exists:
                    print('[SKIPPING] already downloaded')
                    continue

                print('\nDownloading episode {} at {}p'.format(
                    episode_number, source[0]
                ))

                os.system(config['misc']['downloader'].format(
                    dirname=shlex.quote(season_path),
                    filename=shlex.quote(episode_name.format(ext)),
                    filepath=shlex.quote(episode_path.format(ext)),
                    url=shlex.quote(source[1])
                ))

                print('')

                # Now we reload the plex libraries
                if config['plex_reload']['enabled']:
                    base_plex_url = 'http://{}:{}/library/sections'.format(
                        config['plex_reload']['host'],
                        str(config['plex_reload']['port'])
                    )

                    xml_sections = minidom.parseString(
                        requests.get(base_plex_url).text
                    ).getElementsByTagName('Directory')

                    for section in xml_sections:
                        section_title = section.getAttribute('title')

                        if (
                            section_title not in
                            config['plex_reload']['sections'] or
                            len(config['plex_reload']['sections']) <= 0
                        ):
                            continue

                        requests.get('{}/{}/refresh'.format(
                            base_plex_url, section.getAttribute('key')
                        ))

    print('\n:: All done!')
