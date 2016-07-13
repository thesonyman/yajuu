import logging
import os
import glob
import time
import xml.dom.minidom
import urllib.parse
import platform
import re

import magic
import requests
import plexapi.server

from yajuu.config import config
from . import quote

logger = logging.getLogger(__name__)
server = None


def get_plex():
    global server

    if server is None:
        server = plexapi.server.PlexServer(
            config['plex_reload']['base_url'], config['plex_reload']['token']
        )


def download_single_media(path, media_config, media, orchestrator):
    if config['plex_reload']['enabled']:
        get_plex()

    sources = get_sources(media, orchestrator)

    logger.debug(sources)

    path_params = {
        'movie_name': media.metadata['name'],
        'movie_date': media.metadata['year']
    }

    download_file(media, path, media_config['file'], path_params, sources)


def download_season_media(path, media_config, media, seasons, orchestrator):
    if config['plex_reload']['enabled']:
        get_plex()

    sources = get_sources(media, orchestrator)

    for season, season_sources in sources.items():
        season_path = os.path.join(
            os.path.join(path, media.metadata['name']),
            media_config['season'].format(
                season_number=season
            )
        )

        logger.info('Downloading season {}'.format(season))

        for episode_number, sources in season_sources.items():
            logger.info('Downloading episode {}/{} of season {}'.format(
                episode_number, len(media._seasons[season]), season
            ))

            path_params = {
                'anime_name': media.metadata['name'],
                'season_number': season,
                'episode_number': episode_number
            }

            download_file(
                media, season_path, media_config['episode'], path_params,
                sources
            )


def get_sources(media, orchestrator):
    logger.info('-> Starting downloads for media {}'.format(
        media.metadata['name']
    ))

    sources = orchestrator.extract()

    logger.debug('The orchestrator just finished.')
    return sources


def download_file(media, directory, format, path_params, sources):
    if len(glob.glob(format.format(ext='*', **path_params))) > 0:
        logger.info('The file already exists.')
        return

    # We need to know, after iterating over the sources, is the downloaded
    # succeeded or not.
    downloaded = False

    # Since we don't check the extension yet, we can move this out of the loop
    filename = format.format(ext='mp4', **path_params)

    # If the platform is windows, some characters need to be removed
    if platform.system() == 'Windows':
        filename = re.sub(r'[/\\:*?"<>|]', '', filename)
        directory = re.sub(r'[/:*?"<>|]', '', directory)

    path = os.path.join(directory, filename)
    logger.debug('Cleaned path is {}'.format(path))

    if not os.path.exists(directory):
        os.makedirs(directory)

    # Precompile the command params
    command_params = {k: quote(v) for k, v in {
        'dirname': directory,
        'filename': filename,
        'filepath': path
    }.items()}

    sources = filter_sources(sources)
    sources = sort_sources(sources)

    for quality, url in sources:
        netloc = urllib.parse.urlparse(url).netloc

        logger.info('Trying quality {}, downloading from {}'.format(
            quality, netloc
        ))

        command_params['url'] = quote(url)
        command = config['misc']['downloader'].format(**command_params)

        logger.debug(command_params)
        logger.debug(command)

        if os.system(command) == 0:
            # Check the download using magic
            logger.debug('The download succeeded')

            mimetype = magic.from_file(path, mime=True)
            logger.debug(mimetype)

            if mimetype.startswith('video'):
                downloaded = True
                break
            else:
                logger.warning('The downloaded file has a wrong mimetype.')
        else:
            logger.warning('The download failed')

            # Else, delete the remaining file (useful for aria2, wget, ..)
            for to_delete in glob.glob(path + '*'):
                try:
                    os.remove(os.path.join(directory, to_delete))
                    logger.debug('Deleted unnecessary {}'.format(to_delete))
                except OSError as exception:
                    logger.error(exception)
                    logger.warning('Could not delete {}'.format(to_delete))

    if not downloaded:
        logger.error('No valid sources were discovered.')
        return

    if config['plex_reload']['enabled']:
        wanted_sections = config['plex_reload']['sections'][media.get_name()]

        for section in server.library.sections():
            if section.title not in wanted_sections:
                continue

            logger.info('Plex: reloading section "{}"'.format(section.title))
            section.refresh()
    else:
        logger.debug('The plex reloader is disabled.')

    logger.info('')


def filter_sources(sources):
    minimum_quality = config['media']['minimum_quality']
    maximum_quality = config['media']['maximum_quality']

    good_sources = []

    for quality, url in sorted(sources, reverse=True):
        if quality < minimum_quality:
            logger.debug('Skipping too low quality {}'.format(quality))
            continue
        elif maximum_quality > 0 and quality > maximum_quality:
            logger.warning('Skipping quality too high {}'.format(quality))
            continue

        good_sources.append((quality, url))

    return good_sources


def sort_sources(sources):
    '''Sort the available sources by speed.'''

    # First, get the largest url netloc, so we can align the messages
    max_length = 0

    for quality, url in sources:
        host_length = len(urllib.parse.urlparse(url).netloc)

        if host_length > max_length:
            max_length = host_length

    # Then, group the sources in a dict, cause we still want to preserve
    # quality over speed.
    by_quality = {}

    for quality, url in sources:
        if quality not in by_quality:
            by_quality[quality] = []

        by_quality[quality].append(url)

    for quality in sorted(by_quality, reverse=True):
        sources = by_quality[quality]
        chunk_qualities = []

        if len(sources) <= 1:
            logger.debug(
                'Only one source available for this quality, skipping network '
                'speed sort.'
            )

            yield (quality, sources[0])
            continue

        for url in sources:
            netloc = urllib.parse.urlparse(url).netloc
            offset = max_length - len(netloc)

            base = 'Testing source at {}.. {} '.format(
                netloc, ' ' * offset
            )

            response = requests.get(
                url, stream=True, headers={'Connection': 'close'}
            )
            size = 1e6  # Test over 1mb

            start = time.time()
            downloaded = 0

            for chunk in response.iter_content(chunk_size=1024):
                downloaded += len(chunk)

                print('{} {} bytes'.format(
                    base, downloaded
                ), end='\r', flush=True)

                if downloaded >= size:
                    break

            response_time = time.time() - start

            print('{0} {1} bytes downloaded in {2:.2f} seconds'.format(
                base, downloaded, response_time
            ))

            chunk_qualities.append((response_time, url))

        # Now sort the chunk, fastest (smaller) first
        chunk_qualities = sorted(
            chunk_qualities, key=lambda x: x[0]
        )

        logger.debug((quality, chunk_qualities))

        # Remove the response time and re-add the quality
        for response_time, url in chunk_qualities:
            yield (quality, url)
