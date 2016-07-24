import urllib.parse
import sys
import logging

import click
import jinja2
import tldextract

from yajuu.cli.asker import Asker

logger = logging.getLogger(__name__)
asker = Asker.factory()


def generate(type):
    if type == 'extractor':
        env = {}
        env['url'] = asker.text('Enter the url of the website')

        if not env['url']:
            logger.error('No url was provided.')
            sys.exit(1)

        default_class_name, capitalize = '', True

        for character in tldextract.extract(env['url']).domain:
            if character.isalpha() or character.isdigit():
                default_class_name += (
                    character.upper() if capitalize else character
                )

                capitalize = False
            else:
                capitalize = True

        default_class_name += 'Extractor'

        env['class_name'] = asker.text(
            'Enter the name of the class', default=default_class_name
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

        with open('yajuu/cli/dev/templates/extractor.py') as file:
            template = jinja2.Template(file.read())

        print(template.render(**env))
