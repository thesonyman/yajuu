import os
import xml.dom.minidom
import glob
import logging
import time

import click
import requests
import tabulate

from yajuu.media.sources.source import Source
from yajuu.config import config
from yajuu.cli.asker import Asker
from yajuu.cli.media.download.downloader import (
    download_single_media, download_season_media
)
from yajuu.types import MEDIA_TYPES_KEYS

logger = logging.getLogger(__name__)
asker = Asker.factory()
automatic_mode = False


def download(ctx, media, skip_confirmation, automatic, dump):
    global automatic_mode
    automatic_mode = automatic

    # Since we can't change the name
    medias = media
    del media

    # First step
    confirm_download(medias, skip_confirmation)

    orchestrators = create_orchestrators(ctx, medias)

    logger.debug(orchestrators)

    logger.info(
        'Starting the downloads! The process is completely automatic by now, '
        'you can let it run in the background.'
    )

    # The specific media type configuration section
    media_config = config['paths']['medias'][ctx.obj['MEDIA_TYPE']]

    # Specific path for the provided media type
    medias_path = os.path.join(config['paths']['base'], media_config['base'])

    for media_type, data in orchestrators:
        data = list(data)
        data.insert(0, dump)
        data.insert(1, medias_path)
        data.insert(2, media_config)

        if media_type == 'season':
            download_season_media(*data)
        else:
            download_single_media(*data)

    logger.info('\nDone! Yajuu took {} to complete.'.format(
        time.strftime('%H hours, %M minutes and %S seconds', time.gmtime(
            time.time() - ctx.obj['START_TIME']
        ))
    ))

    if dump:
        logger.info(
            'Please note that most links are certainly valid only for a few '
            'hours.'
        )


def confirm_download(medias, skip_confirmation):
    # First, we print out the medias that will be downloaded, so that the user
    # can confirm them.
    logger.info('\nMedias to download now: ')

    to_download_season = []
    to_download_single = []

    for media_type, data in medias:
        if media_type == 'season':
            media, seasons = data

            to_download_season.append((
                media.metadata['name'],
                ', '.join(str(season) for season in seasons)
            ))
        else:
            to_download_single.append((data.metadata['name'],))

    if len(to_download_season) > 0:
        logger.info(tabulate.tabulate(
            to_download_season, headers=['Name', 'Season(s)'], tablefmt='psql'
        ) + '\n')

    if len(to_download_single) > 0:
        if len(to_download_season) > 0:
            logger.info('')

        logger.info(tabulate.tabulate(
            to_download_single, headers=['Name'], tablefmt='psql'
        ) + '\n')

    if not skip_confirmation:
        if not asker.confirm(
            'Do you wish to start the downloads?', default=True
        ):
            logger.debug('Exiting program')
            os._exit(0)
    else:
        logger.debug('Skipping the confirmation.')


def create_orchestrators(ctx, medias):
    # Second step: create the orchestrators. They handle the difficult part:
    # creating the extractors and executing them using threads. We will search
    # on all the orchestrators before downloading anything, that way we'll be
    # able to stop requesting informations from the user.
    orchestrators = []

    for media_type, data in medias:
        # If this is a season media
        if media_type == 'season':
            media, seasons = data

            orchestrator = ctx.obj['ORCHESTRATOR_CLASS'](media, seasons)

            logger.debug('Searching for "{}", season{} {}.'.format(
                media.metadata['name'], 's' if len(seasons) > 1 else '',
                ', '.join(str(s) for s in seasons)
            ))

            # The object holds the data automatically
            orchestrator.search(select_result=select_result)

            orchestrators.append((
                'season', (media, seasons, orchestrator)
            ))
        else:
            orchestrator = ctx.obj['ORCHESTRATOR_CLASS'](data)

            logger.debug('Searching for "{}".'.format(data.metadata['name']))
            orchestrator.search(select_result=select_result)

            orchestrators.append((
                'single', (data, orchestrator)
            ))

    return orchestrators


def select_result(extractor, query, message, results):
    extractor_name = type(extractor).__name__

    logger.debug('{} found {} results'.format(extractor_name, len(results)))

    for key in MEDIA_TYPES_KEYS:
        if extractor.media.get_name().lower() == key:
            break

    default_version = config['paths']['version']
    media_version = config['paths']['medias'][key]['version']

    if media_version != 'any' and default_version != 'any':
        if not media_version or media_version == '':
            media_version = default_version

        version = getattr(Source.VERSIONS, media_version)
        results = [x for x in results if x.version == version]

    if len(results) <= 0:
        logger.debug('The extractor {} did not find any results.'.format(
            extractor_name
        ))

        return None

    media_title = extractor.media.metadata['name'].lower().strip()
    alternate_title = None

    if extractor.media.get_name() == 'Movie':
        media_title = '{} ({})'.format(
            media_title, extractor.media.metadata['year']
        )

    for result in results:
        title = result.title.lower().strip()

        if title == media_title or title == alternate_title:
            logger.info('Found perfect match on {}\n'.format(
                extractor._get_url()
            ))

            return result.identifier

    if automatic_mode:
        return

    return asker.select_one(message, [(
        r.title, r.identifier
    ) for r in results[:20]])
