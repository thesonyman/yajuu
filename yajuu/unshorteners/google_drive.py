import re
import logging

import requests

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    import js2py

    html = requests.get(url).text

    javascript = '{}.split(\'|\')[1]'.format(
        re.search(r'\["fmt_stream_map"\,(".+?")\]', html).group(1)
    )

    logger.debug('Executing: {}'.format(javascript))

    src = js2py.eval_js(javascript)

    logger.debug('[google drive] found source {}'.format(src))

    if quality is None:
        logger.warning('[google drive] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]
