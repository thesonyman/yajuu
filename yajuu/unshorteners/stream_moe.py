import re
import base64
import logging

import requests

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    html = requests.get(url).text
    logger.debug(html)
    frame_html = str(base64.b64decode(
        re.search(r'atob\(\'(.+)\'\)', html).group(1)
    ))

    src = re.search(r'<source src="(.+?)" type="', frame_html).group(1)
    logger.debug('[stream.moe] found source {}'.format(src))

    if quality is None:
        logger.warning('[stream.moe] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]
