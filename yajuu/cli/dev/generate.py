import urllib.parse
import sys
import os
import logging

import click
import jinja2
import tldextract

from yajuu.cli.asker import Asker

logger = logging.getLogger(__name__)
asker = Asker.factory()


def generate(type):
    if type == 'extractor':
        generate_extractor()


def generate_extractor():
    env = {}
    env['url'] = asker.text('Enter the url of the website')

    if not env['url']:
        logger.error('No url was provided.')
        sys.exit(1)

    class_name = ''
    file_name = ''
    is_special = True

    for c in tldextract.extract(env['url']).domain:
        if c.isalpha() or c.isdigit():
            class_name += c.upper() if is_special else c
            file_name += '_' + c if file_name != '' and is_special else c
            is_special = False
        else:
            is_special = True

    class_name += 'Extractor'
    file_name += '.py'

    file_name = asker.text('Enter the filename', default=file_name)
    path = 'yajuu/extractors/anime/{}'.format(file_name)

    if os.path.exists(path):
        logger.error('The file already exists. Exiting.')
        sys.exit(1)

    env['class_name'] = asker.text(
        'Enter the name of the class', default=class_name
    )

    env['disable_cloudflare'] = asker.confirm(
        'Does the website uses the cloudflare protection ?'
    )

    env['import_source'] = asker.confirm(
        'Does the website offer multiple versions or languages?'
    )

    env['import_unshorten'] = asker.confirm(
        'Does the website uses external sites to host files?'
    )

    logger.debug(env)

    with open('yajuu/cli/dev/templates/extractor.py') as file:
        template = jinja2.Template(file.read())

    with open(path, 'w') as file:
        file.write(template.render(**env))

    logger.info('\nThe extractor has been created.')

    orchestrator = 'yajuu/orchestrators/anime/anime_orchestrator.py'

    with open(orchestrator, 'r') as file:
        content = file.read().split('\n')

    import_encountered = False

    import_index = None
    return_index = None

    for index, line in enumerate(content):
        if line.startswith('from yajuu.extractors.'):
            import_index = index + 1

        if '_get_default_extractors' in line and return_index is None:
            return_index = index + 2

    content.insert(
        import_index,
        'from yajuu.extractors.anime.{} import {}'.format(
            file_name[:-3],  # Remove '.py'
            class_name
        )
    )

    content.insert(
        return_index, '        return [{}]\n'.format(class_name)
    )

    with open(orchestrator, 'w') as file:
        file.write('\n'.join(content))

    logger.info(
        'The extractor has been added and selected as the only extractor.'
    )
    logger.warning(
        'Don\'t forget to re-edit the orchestrator when you\'re done.'
    )
