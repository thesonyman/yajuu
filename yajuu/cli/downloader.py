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

        # We need to exclude the first part, C:, D:, ..
        drive, relative = os.path.splitdrive(directory)
        directory = os.path.join(drive, re.sub(r'[/:*?"<>|]', '', relative))

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

    for source in sources.sorted():
        netloc = urllib.parse.urlparse(source.url).netloc

        logger.info('Trying quality {}, downloading from {}'.format(
            source.quality, netloc
        ))

        command_params['url'] = quote(source.url)
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
