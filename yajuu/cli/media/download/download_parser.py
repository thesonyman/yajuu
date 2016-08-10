import logging
import re
import os

import click
import pytvdbapi

from yajuu.media.media import Media
from yajuu.media.season_media import SeasonMedia
from yajuu.cli.asker import Asker

logger = logging.getLogger(__name__)
asker = Asker.factory()


def validate_media(context, param, values):
    '''Provides the necessary method to parse the passed media from the command
    line. This method automatically detects the type of the media passed.'''

    logger.info('Getting the required metadata..')

    try:
        if issubclass(context.obj['MEDIA_CLASS'], SeasonMedia):
            medias = validate_season_media(context, param, values)
        else:
            medias = validate_single_media(context, param, values)
    except KeyboardInterrupt:
        logger.info('Aborted.')
        os._exit(0)

    return medias


def validate_single_media(context, param, values):
    '''Parse the passed medias when they are "single", such as movies.'''

    medias = []

    for value in values:
        query = value.strip()

        try:
            media = context.obj['MEDIA_CLASS'](query)
        except Media.MediaNotFoundException:
            raise click.BadParameter('the media {} was not found'.format(
                query
            ))
        except pytvdbapi.error.ConnectionError:
            logger.error('You\'re not connected to any network.')
            os._exit(1)

        medias.append(('single', media))

    return medias


def validate_season_media(context, param, values):
    '''Parse the passed medias when they have seasons, such as TV Shows.'''

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
            media = context.obj['MEDIA_CLASS'](query)
        except Media.MediaNotFoundException:
            raise click.BadParameter('the media {} was not found'.format(
                query
            ))
        except pytvdbapi.error.ConnectionError:
            logger.error('You\'re not connected to any network.')
            os._exit(1)

        try:
            # Map the seasons to a list of integers.
            seasons = list(map(lambda x: int(x.strip()), parts[1].split(',')))
        except ValueError:
            raise click.BadParameter(
                'a media parameter season part was not formatted as a list of '
                'numbers separated by commas.'
            )

        for season in seasons:
            if season in media.metadata['seasons'].keys():
                continue

            raise click.BadParameter(
                'The season {} for the media "{}" does not exist.'.format(
                    season, media.metadata['name']
                )
            )

        medias.append(('season', (media, seasons)))

    return medias


def select_media(name, results):
    '''The media constructor smoetimes needs to select'''

    return asker.select_one(
        "Which title is correct for input '{}'?".format(name),
        [(x.SeriesName, x) for x in results]
    )
