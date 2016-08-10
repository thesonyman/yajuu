import logging
import re

import requests

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    html = requests.get(url).text
    src = re.search(r'downloadlink: "(.+?)",', html).group(1)

    if quality is None:
        logger.warning('[videonest] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]
