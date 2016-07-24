import re
import base64
import logging

import requests
from bs4 import BeautifulSoup

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    id = re.search(r'https?://bakavideo.tv/embed/(.+)', url).group(1)

    data = requests.get(
        'https://bakavideo.tv/get/files.embed?f={}'.format(id)
    ).json()

    html = base64.b64decode(
        data['content']
    ).decode('utf-8').replace('\n', '').replace('\t', '')

    soup = BeautifulSoup(html, 'html.parser')
    source_div = src = soup.find('source')

    if not source_div:
        return None

    src = source_div.get('src')

    logger.debug('[bakavideo] found source {}'.format(src))

    if quality is None:
        logger.warning('[bakavideo] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]
