import logging
import os
import glob
import time
import xml.dom.minidom
import urllib.parse

import shlex
import requests

from yajuu.config import config

logger = logging.getLogger(__name__)


def download_single_media(path, media_config, media, orchestrator):
    sources = get_sources(media, orchestrator)

    logger.debug(sources)

    path_params = {
        'movie_name': media.metadata['name'],
        'movie_date': media.metadata['year']
    }

    download_file(path, media_config['file'], path_params, sources)

def download_season_media(path, media_config, media, seasons, orchestrator):
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
            logger.info('Downloading episode {}'.format(episode_number))

            path_params = {
                'anime_name': media.metadata['name'],
                'season_number': season,
                'episode_number': episode_number
            }

            download_file(
                season_path, media_config['episode'], path_params, sources
            )

def get_sources(media, orchestrator):
    logger.info('-> Starting downloads for media {}'.format(
        media.metadata['name']
    ))

    sources = orchestrator.extract()

    logger.debug('The orchestrator just finished.')
    return sources

def download_file(directory, format, path_params, sources):
    if len(glob.glob(format.format(ext='*', **path_params))) > 0:
        logger.info('The file already exists.')
        return

    # We need to know, after iterating over the sources, is the downloaded
    # succeeded or not.
    downloaded = False

    # Since we don't check the extension yet, we can move this out of the loop
    filename = format.format(ext='mp4', **path_params)
    path = os.path.join(directory, filename)

    if not os.path.exists(directory):
        os.makedirs(directory)

    # Precompile the command params
    command_params = {k: shlex.quote(v) for k, v in {
        'dirname': directory,
        'filename': filename,
        'filepath': path
    }.items()}

    sources = filter_sources(sources)
    sources = sort_sources(sources)

    for quality, url in sources:
        logger.info('Trying quality {}'.format(quality))

        command_params['url'] = shlex.quote(url)
        command = config['misc']['downloader'].format(**command_params)

        logger.debug(command_params)
        logger.debug(command)

        if os.system(command) == 0:
            logger.debug('The download succeeded')
            downloaded = True
            break
        else:
            logger.warning('The download failed')

    if not downloaded:
        logger.error('No valid sources were discovered.')
        return

    if config['plex_reload']['enabled']:
        base_plex_url = 'http://{}:{}/library/sections'.format(
            config['plex_reload']['host'], str(config['plex_reload']['port'])
        )

        xml_sections = xml.dom.minidom.parseString(
            requests.get(base_plex_url).text
        ).getElementsByTagName('Directory')

        for section in xml_sections:
            section_title = section.getAttribute('title')

            logger.debug('Plex: discovered section {}'.format(section_title))

            if section_title not in config['plex_reload']['sections']:
                continue

            logger.debug('Plex: reloading section {}'.format(section_title))

            key = section.getAttribute('key')

            url = base_plex_url + key + '/refresh'
            logger.debug('Reloading {}'.format(url))
            requests.get(url)
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

    # First, group the sources in a dict, cause we still want to preserve
    # quality over speed.
    by_quality = {}

    for quality, url in sources:
        if quality not in by_quality:
            by_quality[quality] = []

        by_quality[quality].append(url)

    # Then, filter all blocks by speed.
    sorted_qualities = []

    for quality in sorted(by_quality, reverse=True):
        sources = by_quality[quality]
        chunk_qualities = []

        for url in sources:
            base = 'Testing source at {}.. '.format(
                urllib.parse.urlparse(url).netloc
            )

            response = requests.get(url, stream=True)
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
        sorted_qualities += [(quality, x[1]) for x in chunk_qualities]

    return sorted_qualities
