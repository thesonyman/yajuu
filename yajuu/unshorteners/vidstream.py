import logging
import re

import requests
from bs4 import BeautifulSoup

from yajuu.media.sources.source import Source

logger = logging.getLogger()


def unshorten(url, quality=None):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    sources = []

    for link in soup.select('.mirror_link a'):
        sources.append(Source(
            link.get('href'),
            int(re.search(r'Download \((\d+)P - .+', link.text).group(1))
        ))

    logger.debug('[vidstream] found {} sources'.format(len(sources)))

    return sources
