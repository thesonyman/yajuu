import sys
import yaml
import logging

import click
import inquirer
import plexapi.myplex
import plexapi.exceptions

from yajuu.config import config, save_config

logger = logging.getLogger(__name__)


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
    questions = [
        inquirer.Text('username', message="Enter your username"),
        inquirer.Password('password', message="Enter your password")
    ]

    answers = inquirer.prompt(questions)
    logger.info('')

    # Also check for empty values
    if not answers or not answers['username'] or not answers['password']:
        sys.exit(0)

    try:
        account = plexapi.myplex.MyPlexAccount.signin(
            answers['username'], answers['password']
        )
    except plexapi.exceptions.Unauthorized:
        logger.error('Could not login with provided informations.')
        sys.exit(1)

    logger.debug('Auth token is {}'.format(account.authenticationToken))
    return account


def get_plex(account):
    resources = account.resources()

    answers = inquirer.prompt([
        inquirer.List(
            'server',
            message='Which resource is the server you want to reload?',
            choices=[x.name for x in resources]
        )
    ])

    if not answers:
        sys.exit(0)

    selected_server = answers['server']

    server = None

    for resource in resources:
        if resource.name == selected_server:
            server = resource
            break

    return server.connect()


def get_selected_sections(plex):
    sections = plex.library.sections()
    selected_sections = {}

    for media_name in config['plex_reload']['sections']:
        answers = inquirer.prompt([
            inquirer.Checkbox(
                'sections',
                message=(
                    'When a(n) {} is download, which section(s) should be '
                    'reloaded?'
                ).format(media_name.lower()),
                choices=[x.title for x in sections]
            )
        ])

        if not answers:
            sys.exit(0)

        selected_sections[media_name] = answers['sections']

    return selected_sections
