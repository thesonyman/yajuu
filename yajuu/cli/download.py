import click
import sys
import re
import inquirer

from yajuu.media import Anime, Media


def validate_media(context, param, values):
    '''Validates, formats and get from the web the passed medias'''

    print('Getting the required metadata..')

    if len(values) <= 0:
        raise click.BadParameter('no media was specified')

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
            media = Anime(query, select_result=select_media)
        except Media.MediaNotFoundException:
            raise click.BadParameter('the media {} was not found'.format(
                query
            ))

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

        medias.append((media, seasons))

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
@click.option('--media', callback=validate_media, multiple=True)
def download(media):
    click.echo(str(media))
