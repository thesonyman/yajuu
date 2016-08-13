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
        value = value.strip()

        # We need to extract the ranges
        ranges = None

        results = re.search(
            r'( \((?:\s*(from episode)* \d+( to \d+)*( for season \d+)*\s*'
            r'[\)\,])+)$',
            value
        )

        if results:
            # Strip the ranges part from the value
            value = value[:-len(results.group(1))]

            ranges = {}

            for part in results.group(1).split(','):
                range_results = re.search(
                    r'(?:from episode)* ([1-9]+\d*)(?: to ([1-9]+\d*))*(?: for'
                    r' season ([1-9]+\d*))*', part
                )

                try:
                    season = int(range_results.group(3))
                except (AttributeError, TypeError):
                    season = None

                try:
                    start = int(range_results.group(1))
                except AttributeError:
                    raise click.BadParameter(
                        'One of the passed range had a bad number (leading '
                        'with zero?).'
                    )

                try:
                    end = int(range_results.group(2))
                except (AttributeError, TypeError):
                    end = None

                if season in ranges:
                    raise click.BadParameter(
                        'A season was repeated in the range.'
                    )

                if end is not None and start > end:
                    raise click.BadParameter(
                        'The start is superior to the end on one of the '
                        'provided ranges.'
                    )

                ranges[season] = [start, end]

            if list(ranges.keys()).count(None) >= 1:
                if len(ranges) <= 1:
                    data = ranges[list(ranges.keys())[0]]
                    del ranges[list(ranges.keys())[0]]
                    ranges[1] = data
                else:
                    raise click.BadParameter(
                        'More than one range was specified when one is missing'
                        ' a range.'
                    )

        # The order seasonS before season matters, that way we won't have a
        # trailing 's' in the second part.
        parts = re.split(' seasons | season ', value)

        if len(parts) != 2:
            raise click.BadParameter(
                'a media parameter was not formatted as "name season seasons"'
            )

        try:
            # Map the seasons to a list of integers.
            seasons = list(map(lambda x: int(x.strip()), parts[1].split(',')))
        except ValueError:
            raise click.BadParameter(
                'a media parameter season part was not formatted as a list of '
                'numbers separated by commas.'
            )

        if ranges:
            for range_season in ranges:
                if range_season not in seasons:
                    raise click.BadParameter(
                        'A range was specified for a season that was not specified'
                        '.'
                    )
        else:
            ranges = {}

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

        for season in seasons:
            if season not in media.metadata['seasons'].keys():
                raise click.BadParameter(
                    'The season {} for the media "{}" does not exist.'.format(
                        season, media.metadata['name']
                    )
                )

            episodes = media.metadata['seasons'][season]

            if season in ranges:
                start, end = ranges[season]

                if end is None:
                    last = max(list(episodes.keys()))
                    end = last
                    ranges[season][1] = end

                if start not in episodes or end not in episodes:
                    raise click.BadParameter(
                        'The range is invalid for the media {}, season {}: the'
                        ' episode {} or {} does not exists.'.format(
                            media.metadata['name'], season, start, end
                        )
                    )
            else:
                episode_numbers = list(episodes.keys())
                ranges[season] = [min(episode_numbers), max(episode_numbers)]

        medias.append(('season', (media, ranges)))

    return medias


def select_media(name, results):
    '''The media constructor smoetimes needs to select'''

    return asker.select_one(
        "Which title is correct for input '{}'?".format(name),
        [(x.SeriesName, x) for x in results]
    )
