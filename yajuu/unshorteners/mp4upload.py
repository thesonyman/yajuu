import re
import logging

import requests

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    html = requests.get(url).text

    if 'File was deleted' in html:
        logger.warning('[mp4upload] File at {} was deleted'.format(url))
        return []

    src = re.search(r'"file": "(.+)"', html).group(1)

    if quality is None:
        logger.warning('[mp4upload] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]
