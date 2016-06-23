import sys
import re
import logging

import click
import inquirer
import pytvdbapi
import tabulate

from yajuu.media import Media

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
    # creating the extractors and executing them using threads.
    for media, seasons in medias:
        orchestrator = ctx.obj['ORCHESTRATOR_CLASS'](media, seasons)

        logger.debug('Searching for "{}", season{} {}.'.format(
            media.metadata['name'], 's' if len(seasons) > 1 else '',
            ', '.join(str(s) for s in seasons)
        ))
