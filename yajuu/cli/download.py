import sys
import os
import re
import xml.dom.minidom
import glob
import logging

import click
import shlex
import requests
import inquirer
import pytvdbapi
import tabulate

from yajuu.media import Media
from yajuu.config import config

logger = logging.getLogger(__name__)


def validate_media(context, param, values):
    '''Validates, formats and get from the web the passed medias'''

    logger.info('Getting the required metadata..')

    medias = []

    for value in values:
        # The order seasonS before season matters, that way we won't have a
        # trailing 's' in the second part.
        parts = re.split(' seasons | season ', value)

        if len(parts) != 2:
            raise click.BadParameter(
                'a media parameter was not formatted as "name season seasons"'
            )

        query = parts[0].strip()

        try:
            media = context.obj['MEDIA_CLASS'](
                query, select_result=select_media
            )
        except Media.MediaNotFoundException:
            raise click.BadParameter('the media {} was not found'.format(
                query
            ))
        except pytvdbapi.error.ConnectionError:
            logger.error('You\'re not connected to any network.')
            sys.exit(1)

        try:
            # Map the seasons to a list of integers.
            seasons = list(map(lambda x: int(x.strip()), parts[1].split(',')))
        except ValueError:
            raise click.BadParameter(
                'a media parameter season part was not formatted as a list of '
                'numbers separated by commas.'
            )

        for season in seasons:
            if season in media.get_seasons():
                continue

            raise click.BadParameter(
                'The season {} for the media "{}" does not exist.'.format(
                    season, media.metadata['name']
                )
            )

        medias.append([media, seasons])

    return medias

@click.command()
@click.pass_context
@click.option(
    '--media', callback=validate_media, multiple=True, required=True,
    help='Add a media to download, the string must respect the format "Name '
    'season[s] s,..". Eg: "Code Geass" seasons 1,2. The option can be passed '
    'multiple times.'
)
@click.option(
    '--skip-confirmation', is_flag=True, help='Skip the first confirmation, '
    'however you will still need to select the correct results'
)
def download(ctx, media, skip_confirmation):
    # Since we can't change the name
    medias = media
    del media

    # First, we print out the medias that will be downloaded, so that the user
    # can confirm them.
    logger.info('\nMedias to download now: ')

    # Generate a list similar to the medias list, only the first variable fo
    # each element is the name of the media, and the second is a list of all
    # the seasons formatted as a string.
    to_download = [
        (media.metadata['name'], ', '.join(str(season) for season in seasons))
        for media, seasons in medias
    ]

    logger.info(tabulate.tabulate(
        to_download, headers=['Name', 'Season(s)'], tablefmt='psql'
    ) + '\n')

    if not skip_confirmation:
        confirm_question = inquirer.Confirm(
            'continue', message='Do you wish to start the downloads?',
            default=True
        )

        if not inquirer.prompt([confirm_question])['continue']:
            logger.debug('Exiting program')
            sys.exit(0)
    else:
        logger.debug('Skipping the confirmation.')

    # Second step: create the orchestrators. They handle the difficult part:
    # creating the extractors and executing them using threads. We will search
    # on all the orchestrators before downloading anything, that way we'll be
    # able to stop requesting informations from the user.
    orchestrators = []

    for media, seasons in medias:
        orchestrator = ctx.obj['ORCHESTRATOR_CLASS'](media, seasons)

        logger.debug('Searching for "{}", season{} {}.'.format(
            media.metadata['name'], 's' if len(seasons) > 1 else '',
            ', '.join(str(s) for s in seasons)
        ))

        # The object holds the data automatically
        orchestrator.search(select_result=select_result)

        orchestrators.append((media, seasons, orchestrator))

    logger.debug(orchestrators)

    logger.info(
        'Starting the downloads! The process is completely automatic by now, '
        'you can let it run in the background.'
    )

    # The specific media type configuration section
    media_config = config['paths']['medias'][ctx.obj['MEDIA_TYPE']]

    # Specific path for the provided media type
    medias_path = os.path.join(config['paths']['base'], media_config['base'])

    for media, seasons, orchestrator in orchestrators:
        media_path = os.path.join(medias_path, media.metadata['name'])

        logger.info('-> Starting downloads for media {}'.format(
            media.metadata['name']
        ))

        logger.info('Starting the extract phase')

        media_sources = orchestrator.extract()

        logger.debug('The extract is done')

        for season, season_sources in media_sources.items():
            season_path = os.path.join(
                media_path,
                media_config['season'].format(
                    season_number=season
                )
            )

            if not os.path.exists(season_path):
                logger.debug('Creating path {}'.format(season_path))
                os.makedirs(season_path)
            else:
                logger.debug('The path {} already exists'.format(season_path))

            logger.info('Downloading season {}'.format(season))

            for episode_number, sources in season_sources.items():
                download_episode(
                    media, media_config, season, season_path, episode_number,
                    sources
                )

def select_media(name, results):
    question = inquirer.List('name',
        message="Which title is correct for input '{}'?".format(name),
        choices=list(x.SeriesName for x in results)
    )

    answers = inquirer.prompt([question])

    # If the user aborted
    if not answers:
        sys.exit(0)

    for result in results:
        if result.SeriesName == answers['name']:
            return result

    return None

def select_result(extractor, query, message, results):
    extractor_name = type(extractor).__name__

    logger.debug('{} found {}'.format(extractor_name, results))

    results = results[:20]

    if len(results)  <= 0:
        logger.debug('The extractor {} did not find any results.'.format(
            extractor_name
        ))

        return None

    question = inquirer.List('result',
        message=message,
        choices=list(x[0] for x in results)
    )

    answers = inquirer.prompt([question])

    if not answers or not answers['result']:
        return None

    for result in results:
        if result[0] == answers['result']:
            return result

    return None

def filter_quality(source):
    minimum_quality = config['media']['minimum_quality']
    maximum_quality = config['media']['maximum_quality']

    quality = source[0]

    if quality < minimum_quality:
        return False
    elif maximum_quality > 0 and quality > maximum_quality:
        return False

    return True

def download_episode(
    media, media_config, season, season_path, episode_number, sources
):
    '''Since 4 nested for loops is pretty hard to read, we separate the logic
    to download an episode in another episode.'''

    logger.info('Downloading episode {}'.format(episode_number))

    sources = list(filter(filter_quality, sources))
    logger.debug('Correct sources: {}'.format(sources))

    if len(sources) <= 0:
        logger.warning('No valid sources were found.')
        return

    path_params = {
        'anime_name': media.metadata['name'],
        'season_number': season,
        'episode_number': episode_number
    }

    episode_format = media_config['episode']

    if len(glob.glob(episode_format.format(**path_params, ext='*'))) > 0:
        logger.info('A file already exists, skipping!')
        return

    downloaded = False

    for quality, url in sorted(sources, reverse=True):
        logger.info('Trying quality {}'.format(quality))

        episode_name = episode_format.format(**path_params, ext='mp4')

        episode_path = os.path.join(
            season_path,
            episode_name
        )

        command = config['misc']['downloader'].format(
            dirname=shlex.quote(season_path),
            filename=shlex.quote(episode_name),
            filepath=shlex.quote(episode_path),
            url=shlex.quote(url)
        )

        logger.debug(command)

        if os.system(command) == 0:
            logger.debug('The download succeeded.')
            downloaded = True
            break
        else:
            logger.warning('The download failed')

    if not downloaded:
        logger.error('No download succeeded.')
    elif config['plex_reload']['enabled']:
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
            requests.get(base_plex_url + key + '/refresh')
    else:
        logger.debug('Plex: the reloader is disabled')

    logger.info('')
