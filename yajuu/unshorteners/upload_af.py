import logging

import requests
from bs4 import BeautifulSoup

from yajuu.unshorteners.utils import get_quality
from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    if not url.startswith('https'):
        url = 'https' + url[4:]

    def get_payload(source, selector, fields):
        soup = BeautifulSoup(source, 'html.parser')
        form = soup.select(selector)

        payload = {}

        for input in soup.find_all('input'):
            if input.get('name') not in fields:
                continue

            payload[input.get('name')] = input.get('value')

        return payload

    download_1_payload = get_payload(
        requests.get(url).text, 'form',
        ['op', 'usr_login', 'id', 'fname', 'referer', 'method_free']
    )

    download_2_payload = get_payload(
        requests.post(url, data=download_1_payload).text, 'form[name="F1"]',
        ['op', 'usr_login', 'id', 'fname', 'referer', 'method_free']
    )

    soup = BeautifulSoup(
        requests.post(url, data=download_2_payload).text,
        'html.parser'
    )

    src = soup.select('.text-center a')[0].get('href')

    if quality is None:
        logger.warning('[upload.af] quality was not passed')
        quality = get_quality(src)

    return [Source(src, quality)]
