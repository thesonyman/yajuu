import os
import subprocess
import tempfile
import tempfile

import click
import logging
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)
TEMP = []


def shell():
    try:
        from IPython import embed, start_ipython
    except ImportError:
        logger.error('Could not find ipython. Please install it.')
        os._exit(0)

    try:
        start_ipython(argv=[], user_ns={
            'requests': requests,
            'BeautifulSoup': BeautifulSoup,
            'visualize': visualize
        })
    finally:
        for fd, path in TEMP:
            logger.debug('Removing temp file {}'.format(path))
            os.close(fd)
            os.remove(path)


def visualize(response):
    if isinstance(response, BeautifulSoup):
        response = response.prettify()
    elif isinstance(response, requests.models.Response):
        response = response.text

    fd, path = tempfile.mkstemp(suffix='.html')

    with open(path, 'w') as file:
        file.write(response)

    process = subprocess.Popen(['xdg-open', path])
    process.communicate()

    TEMP.append((fd, path))
