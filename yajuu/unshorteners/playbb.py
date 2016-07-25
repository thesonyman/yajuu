import urllib.parse
import re
import base64
import logging

import requests

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    source = requests.get(url).text

    # Quoted url to a page that redirects to the source
    quoted_url = re.search(r'_url = "(.+?)";', source).group(1)

    query_string = urllib.parse.urlparse(
        urllib.parse.unquote(quoted_url)
    ).query

    # The script just redirect by decoding the passed base64 url
    encoded_url = urllib.parse.parse_qs(query_string)['url'][0]
    src = base64.b64decode(encoded_url).decode('utf-8')

    if quality is None:
        logger.warning('[playbb] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]
