# http://tiwi.kiwi/embed-vd9reskx9q8i.html

import re
import logging

import requests
from bs4 import BeautifulSoup

from yajuu.sources import SourceList, Source
from yajuu.link_handler import extract_pattern


@extract_pattern(r'^https?:\/\/tiwi.kiwi\/(?:embed-)?(.+)(?:\.html)?(?:#.+)?$')
def handle_link(identifier, *args, **kwargs):
    soup = BeautifulSoup(
        requests.get('http://tiwi.kiwi/{}.html'.format(identifier)).text,
        'html.parser'
    )

    sources = SourceList()

    for download_link in soup.find('table', {'class': 'tbl1'}).find_all('a'):
        results = re.search(
            r'download_video\(\'(.+)\',\'(.+)\',\'(.+)\'\)',
            download_link.get('onclick')
        )

        url = 'http://tiwi.kiwi/dl?op=download_orig&id={}&mode={}&hash={}'.format(
            results.group(1), results.group(2), results.group(3)
        )

        soup = BeautifulSoup(requests.get(url).text, 'html.parser')
        src = soup.find('a', {'class': 'btn green'}).get('href')

        sources.add(Source(src, *args, **kwargs))

    return sources
