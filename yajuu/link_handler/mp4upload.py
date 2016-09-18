# http://www.mp4upload.com/xnr19lg02oym

import re
import logging

import requests
from bs4 import BeautifulSoup

from yajuu.sources import SourceList, Source


def handle_link(url, *args, **kwargs):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    fields = ['op', 'id', 'rand', 'referer', 'method_free', 'method_premium']
    payload = {x: soup.find('input', {'name': x}).get('value') for x in fields}

    headers = requests.post(url, data=payload, allow_redirects=False).headers
    src = headers['Location']

    if 'quality' not in kwargs:
        resolution = soup.find(
            'span', text=re.compile(r'\d+ x \d+')
        ).text

        kwargs['quality'] = int(resolution.split('x')[1].strip())

    return SourceList([
        Source(src, *args, **kwargs)
    ])
