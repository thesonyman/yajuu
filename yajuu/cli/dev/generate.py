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


def get_filename(url, extension):
    filename = ''
    is_special = False

    for c in tldextract.extract(url).domain:
        if c.isalpha():
            filename += '_' + c if is_special else c
            is_special = False
        else:
            is_special = True

    return filename + '.' + extension


def get_classname(url, suffix):
    class_name = ''
    is_special = True

    for c in tldextract.extract(url).domain:
        if c.isalpha():
            class_name += c.upper() if is_special else c
            is_special = False
        else:
            is_special = True

    return class_name + suffix


def generate_unshortener():
    env = {}
    env['url'] = asker.text('Enter the url of the website')

    filename = get_filename(env['url'], 'py')
    filename = asker.text('Enter the filename', default=filename)
    path = 'yajuu/unshorteners/' + filename
    env['name'] = filename[:-3]

    parts = tldextract.extract(env['url'])
    host = parts.domain + '.' + parts.suffix
    host = asker.text('Enter the host (stripped from www.)', default=host)

    if os.path.exists(path):
        logger.error('The file already exists.')
        sys.exit(1)

    with open('yajuu/cli/dev/templates/unshortener.py', 'r') as file:
        template = jinja2.Template(file.read())

    with open(path, 'w') as file:
        file.write(template.render(**env))

    with open('yajuu/unshorteners/__init__.py', 'r') as file:
        lines = file.read().split('\n')

    in_dict = False

    for i, line in enumerate(lines):
        if 'unshorteners = {' in line:
            in_dict = True

        if line.strip() == '}' and in_dict:
            in_dict = False
            break

    # Add a comma if necessary to the previous item
    if not lines[i - 1].endswith(','):
        lines[i - 1] += ','

    lines.insert(i, "{}'{}': '{}'".format(
        ' ' * 8, host, env['name']
    ))

    with open('yajuu/unshorteners/__init__.py', 'w') as file:
        file.write('\n'.join(lines))

    logger.info('The files were written.')


def generate_extractor(media_type):
    env = {}
    env['url'] = asker.text('Enter the url of the website')

    if not env['url']:
        logger.error('No url was provided.')
        sys.exit(1)

    class_name = get_classname(env['url'], 'Extractor')
    file_name = get_filename(env['url'], 'py')

    file_name = asker.text('Enter the filename', default=file_name)
    path = 'yajuu/extractors/{}/{}'.format(media_type, file_name)

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

    orchestrator = 'yajuu/orchestrators/{}_orchestrator.py'.format(
        media_type
    )

    with open(orchestrator, 'r') as file:
        lines = file.read().split('\n')

    import_encountered = False
    import_index = None

    return_encountered = False
    return_index = None

    for i, line in enumerate(lines):
        if line.startswith('from yajuu.extractors.'):
            import_encountered = True
        elif import_encountered:
            import_index = i
            import_encountered = False

        if line.strip() == 'return [':
            return_encountered = True
        elif line.strip() == ']' and return_encountered:
            return_index = i
            return_encountered = False

    lines.insert(import_index, 'from yajuu.extractors.{}.{} import {}'.format(
        media_type, file_name[:-3], env['class_name']
    ))

    if not lines[return_index].endswith(','):
        lines[return_index] += ','

    if len(lines[return_index] + ' ' + env['class_name']) > 80:
        lines.insert(return_index + 1, ' ' * 4 * 3 + env['class_name'])
    else:
        lines[return_index] += ' ' + env['class_name']

    with open(orchestrator, 'w') as file:
        file.write('\n'.join(lines))

    logger.info('The extractor has been added to the orchestrator.')
