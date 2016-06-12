'''Provides an entry point for the media command.'''

import os
import re
import sys
import shlex
import urllib.parse
import glob
import shutil
import subprocess
from xml.dom import minidom
import difflib

import tabulate
import requests

from yajuu.media import Anime
from yajuu.config import config
from yajuu.extractors.unshorten import get_quality
from .utils import select, confirm, select_best_result
from yajuu.extractors.anime.anime_orchestrator import AnimeOrchestrator
from yajuu.extractors.anime.htvanime import HtvanimeExtractor
from yajuu.extractors.anime.anime_haven import AnimeHavenExtractor
from yajuu.extractors.anime.anime_chiby import AnimeChibyExtractor
from yajuu.extractors.anime.gogoanime_io import GogoAnimeIoExtractor

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
    elif arguments['repair']:
        _handle_media_repair(media)
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


def _get_downloaded_medias(media, media_class):
    '''Get the download medias, and return them as a dict.'''

    message = 'Getting the needed metadata'
    print(message + '..', end='\r')

    # List of the found medias
    medias = {}

    base_path = os.path.join(
        config['paths']['base'],
        config['paths']['medias'][media]['base']
    )

    folders = next(os.walk(base_path))[1]

    for index, path in enumerate(folders):
        print(message + ' ({}/{})..'.format(index + 1, len(folders)), end='\r')

        media_name = os.path.basename(os.path.normpath(path))
        media = media_class(media_name, select_result=select_best_result)
        realpath = os.path.join(base_path, media_name)

        medias[realpath] = media

    # We add the needed spaces to clear out the formatted output
    print(message + '.. done' + ' ' * (
        (len(str(len(folders))) * 2 + 6) - len('.. done')
    ))

    return medias


def _handle_media_repair(media):
    medias = _get_downloaded_medias(media, Anime)

    # We generate a regex from the config, by replacing the season number part
    # with a regex part.
    season_regex = re.compile(re.sub(
        '{season_number:.+?}', '(\d+)',
        config['paths']['medias'][media]['season']
    ))

    # for path, anime in [('/home/plex/Anime/Jormungand', Anime('Jormungand'))]:
    for path, anime in medias.items():
        # And do the same with the episode part.
        episode_regex = re.compile(re.sub(
            '(?:{season_number:.+?})|(?:{episode_number:.+?})', '(\d+)',
            config['paths']['medias'][media]['episode']
        ).format(
            anime_name=anime.metadata['name'], ext='(?:.+)'
        ))

        # We list all the files that we will find. That way we will be able to
        # determine to missing files.
        found = {}
        download = []

        for folder in next(os.walk(path))[1]:
            season_regex_result = season_regex.search(folder)

            if not season_regex_result:
                _handle_invalid(media, path, folder, 'folder')
                continue

            season_number = int(season_regex_result.group(1))

            # Now we can check the episodes
            for episode_path in os.listdir(os.path.join(path, folder)):
                realpath = os.path.join(path, folder, episode_path)

                episode_regex_result = episode_regex.search(episode_path)

                if not episode_regex_result:
                    _handle_invalid(
                        media, os.path.join(path, folder), episode_path, 'file'
                    )

                    continue

                if os.path.getsize(realpath) <= 5e7:
                    _handle_low_size(episode_path, realpath)
                    continue

                video_quality = get_quality(realpath, quote=False)

                if video_quality < config['media']['minimum_quality']:
                    if _handle_wrong_quality(
                        episode_path, realpath, video_quality, 'low'
                    ):
                        if season_number not in download:
                            download.append(season_number)

                elif (
                    config['media']['maximum_quality'] > 0 and
                    video_quality > config['media']['maximum_quality']
                ):
                    if _handle_wrong_quality(
                        episode_path, realpath, video_quality, 'big'
                    ):
                        if season_number not in download:
                            download.append(season_number)

        print('=>', download)


def _handle_invalid(media, path, folder, type):
    '''Let the user take action after an invalid folder has been detected.'''

    print(
        '\nThe {} "{}" for the media "{}" does not match with your '
        'configuration.'.format(
            type, folder, os.path.basename(os.path.normpath(path))
        )
    )

    done = False

    while not done:
        menu = [
            ('Do nothing', 'nothing'),
            ('Rename the {}'.format(type), 'rename'),
            ('Delete the {}'.format(type), 'delete')
        ]

        action = select('Please select the desired action', menu)[1]

        if action == 'rename':
            new_name = input(':: Please enter the new name: ')

            os.rename(
                os.path.join(path, folder), os.path.join(path, new_name)
            )

            done = True

        elif action == 'delete':
            confirmed = confirm(
                'Do you really want to delete this {}?'.format(type),
                default=False
            )

            if confirmed:
                if type == 'folder':
                    shutil.rmtree(os.path.join(path, folder))
                else:
                    os.remove(os.path.join(path, folder))

                done = True

        elif action == 'nothing':
            done = True

        print('')


def _handle_low_size(name, path):
    print('\n{} is below 50 megabytes, which seems rather low.'.format(
        name
    ))

    menu = [
        ('Do nothing', 'nothing'),
        ('Open the video', 'open'),
        ('Delete the file', 'delete')
    ]

    done = False

    while not done:
        action = select('Please select the desired action', menu)[1]

        if action == 'open':
            subprocess.Popen(['xdg-open', path])
        elif action == 'delete':
            confirmed = confirm(
                'Do you really want to delete this file?',
                default=False
            )

            if confirmed:
                os.remove(path)
                done = True
        elif action == 'nothing':
            done = True

        print('')


def _handle_wrong_quality(name, path, quality, type):
    print((
        '\nThe video {} have a too {} quality compared to your configuration.'
    ).format(name, type))

    menu = [
        ('Delete and schedule for re-download', 'download'),
        ('Do nothing', 'nothing'),
        ('Delete the file', 'delete')
    ]

    done = False

    while not done:
        action = select('Please select the desired action', menu)[1]

        if action == 'open':
            subprocess.Popen(['xdg-open', path])
        elif action == 'download':
            confirmed = confirm(
                'Do you really want to delete this file?',
                default=False
            )

            if confirmed:
                os.remove(path)
                done = True

                print('')
                return True

        elif action == 'delete':
            confirmed = confirm(
                'Do you really want to delete this file?',
                default=False
            )

            if confirmed:
                os.remove(path)
                done = True
        elif action == 'nothing':
            done = True

        print('')

    return False


def _handle_media_list(media, repair):
    anime_path = os.path.join(
         config['paths']['base'], config['paths']['medias']['anime']['base']
    )

    if repair:
        print('Getting the needed metadata..')

    def handle_invalid_file(self, path):
        pass

    animes = {}

    print('Your currently downloaded (even partially) animes are:')

    for folder in glob.glob(os.path.join(anime_path, '*/')):
        anime_name = os.path.basename(os.path.normpath(folder))
        anime = Anime(anime_name, select_result=select_best_result)

        # Get as a list the available seasons
        available_seasons = list(dict(iter(anime)).keys())

        # Get as a list the downloaded seasons (just by listing the folders)
        downloaded_seasons = list(
            int(''.join(
                x for x in os.path.basename(os.path.normpath(x)) if x.isdigit()
            )) for x in glob.glob(os.path.join(
                anime_path, anime_name, 'Season *'
            ))
        )

        # We keep the anime, and the downloaded seasons that are valid
        animes[anime_name] = {
            'anime': anime,
            'seasons': (available_seasons, downloaded_seasons),

            # Holds the seasons then episodes. We first assume that all the
            # seasons are missing.
            'missing': {x: None for x in downloaded_seasons},
        }

        print(' - {} ({}/{} seasons)'.format(
            anime.metadata['name'],
            len(downloaded_seasons),
            len(available_seasons)
        ))

        # Now we will determine the missing seasons and episodes
        for season in available_seasons:
            if season not in downloaded_seasons:
                continue

            available_episodes = list(
                x.number for x in anime.get_season(season).values()
            )

            # We do the same, assume that all the episodes are missing
            animes[anime_name]['missing'][season] = {
                x: None for x in available_episodes
            }

            for episode_path in glob.glob(os.path.join(
                anime_path, anime_name, 'Season {0:02d}'.format(season), '*'
            )):
                ep_template = config['paths']['medias']['anime']['episode']

                ep_number_regex = re.compile(ep_template.format(
                    anime_name='.+', season_number=season,
                    episode_number=-11111,
                    ext=os.path.splitext(episode_path)[1][1:]
                ).replace('-11111', '(\d+)'))

                ep_number_results = ep_number_regex.search(episode_path)

                if ep_number_results:
                    if os.path.getsize(episode_path) <= 1000:
                        print('NO SIZE')
                    else:
                        ep_number = int(ep_number_results.group(1))

                        if ep_number not in available_episodes:
                            print('INVALID EPISODE NUMBER')
                        else:
                            print('VALID')
                else:
                    handle_invalid_file(episode_path)

                import sys
                sys.exit(0)

            # animes[anime_name]['missing'][season]


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
        orchestrator = AnimeOrchestrator([
            HtvanimeExtractor, AnimeChibyExtractor, AnimeHavenExtractor,
            GogoAnimeIoExtractor
        ], anime, season)

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
            print('\n=> Season {0:02d}'.format(season))

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
