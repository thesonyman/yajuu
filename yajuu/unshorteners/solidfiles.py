import logging

import requests
from bs4 import BeautifulSoup

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    link = soup.find('a', {'id': 'download-btn'}).get('href')

    logger.debug('[solidfiles] Found {}'.format(link))

    if quality is None:
        quality = get_quality(link)

    return [Source(link, quality)]
