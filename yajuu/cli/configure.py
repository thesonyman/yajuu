import sys
import yaml
import logging

import click
import plexapi.myplex
import plexapi.exceptions

from yajuu.config import config, save_config
from yajuu.cli import Asker

logger = logging.getLogger(__name__)
asker = Asker.factory()


@click.command()
@click.option(
    '--only-print', is_flag=True,
    help='Only print the configuration as yaml, does not save it.'
)
def plex(only_print):
    account = get_plex_account()
    plex = get_plex(account)
    selected_sections = get_selected_sections(plex)

    config['plex_reload'] = {
        'enabled': True,
        'token': account.authenticationToken,
        'base_url': plex.baseurl,
        'sections': selected_sections
    }

    if only_print:
        print_config = {'plex_reload': config['plex_reload']}
        logger.info(yaml.dump(print_config, default_flow_style=False))
    else:
        save_config()
        logger.info('The configuration has been updated.')


def get_plex_account():
    username = asker.text("Enter your username")
    password = asker.text("Enter your password", hidden=True)

    logger.info('')

    # Also check for empty values
    if not username or not password:
        sys.exit(0)

    try:
        account = plexapi.myplex.MyPlexAccount.signin(
            username, password
        )
    except plexapi.exceptions.Unauthorized:
        logger.error('Could not login with provided informations.')
        sys.exit(1)

    logger.debug('Auth token is {}'.format(account.authenticationToken))
    return account


def get_plex(account):
    resources = account.resources()

    server = asker.select_one(
        'Which resource is the server you want to reload?',
        [(x.name, x) for x in resources]
    )

    if server:
        return server.connect()

    return None


def get_selected_sections(plex):
    sections = plex.library.sections()
    selected_sections = {}

    for media_name in config['plex_reload']['sections']:
        message = (
            'When a(n) {} is download, which section(s) should be reloaded?'
        ).format(media_name.lower())

        selected = asker.select_multiple(
            message,
            [(x.title, x.title) for x in sections]
        )

        if not selected:
            sys.exit(0)

        selected_sections[media_name] = selected

    return selected_sections
