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
from yajuu.cli.utils import quote

logger = logging.getLogger(__name__)
server = None


def get_plex():
    global server

    if server is None:
        server = plexapi.server.PlexServer(
            config['plex_reload']['base_url'], config['plex_reload']['token']
        )


def download_media(dump, path, media_config, media, orchestrator):
    if config['plex_reload']['enabled']:
        get_plex()

    logger.info('-> Starting downloads for media {}'.format(
        media.metadata['name']
    ))

    sources = orchestrator.extract()

    logger.debug('The orchestrator just finished.')
    logger.debug(sources)

    media.download(sources, dump=dump)



def download_file(dump, media, format, path_params, sources, directory=None):
    if len(glob.glob(format.format(ext='*', **path_params))) > 0:
        logger.info('The file already exists.')
        return

    # Get the directory to download the file
    if directory is None:
        media_config = media.get_path_config()
        directory = os.path.join(config['paths']['base'], media_config['base'])

    # We need to know, after iterating over the sources, is the downloaded
    # succeeded or not.
    downloaded = False

    # Since we don't check the extension yet, we can move this out of the loop
    filename = format.format(ext='txt' if dump else 'mp4', **path_params)

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

    if dump:
        with open(path, 'w') as file:
            file.write('\n'.join([x.url for x in sources]))

        return

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
