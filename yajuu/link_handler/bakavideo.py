# https://bakavideo.tv/embed/09E9Ba7DI

import base64

import requests
from bs4 import BeautifulSoup

from yajuu.sources import SourceList, Source
from yajuu.link_handler import extract_pattern


@extract_pattern(r'https?://bakavideo.tv/embed/(.+)$')
def handle_link(identifier, *args, **kwargs):
    data = requests.get(
        'https://bakavideo.tv/get/files.embed?f={}'.format(identifier)
    ).json()

    html = base64.b64decode(
        data['content']
    ).decode('utf-8').replace('\n', '').replace('\t', '')

    soup = BeautifulSoup(html, 'html.parser')
    source_div = soup.find('source')

    if not source_div:
        return None

    sources = SourceList()
    sources.add(Source(source_div.get('src'), *args, **kwargs))
    return sources
