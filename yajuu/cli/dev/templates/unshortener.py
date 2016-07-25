import logging

import requests
from bs4 import BeautifulSoup

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    src = ''

    if quality is None:
        logger.warning('[{{name}}] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]

