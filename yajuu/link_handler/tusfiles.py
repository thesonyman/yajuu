# http://www.tusfiles.net/jl1b0u5g941v

import requests
from bs4 import BeautifulSoup

from yajuu.sources import SourceList, Source


def handle_link(url, *args, **kwargs):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    form = soup.find('form', {'name': 'F1'})

    fields = ['op', 'id', 'rand', 'referer', 'method_free', 'method_premium']
    payload = {x: soup.find('input', {'name': x}).get('value') for x in fields}

    src = requests.post(url, data=payload, stream=True).url

    return SourceList([
        Source(src, *args, **kwargs)
    ])
