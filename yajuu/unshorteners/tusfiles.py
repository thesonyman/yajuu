import logging

import requests
from bs4 import BeautifulSoup

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    form = soup.find('form', {'name': 'F1'})

    payload = {}
    fields = ['op', 'id', 'rand', 'referer', 'method_free', 'method_premium']

    for input in form.select('input'):
        if input.get('name') not in fields:
            continue

        payload[input.get('name')] = input.get('value')

    logger.debug('[tufiles] {}'.format(payload))

    src = requests.post(url, data=payload, stream=True).url

    if quality is None:
        logger.warning('[tusfiles] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]
