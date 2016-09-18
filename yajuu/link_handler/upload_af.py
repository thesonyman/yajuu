# https://upload.af/i27gmu6jofvw

import requests
from bs4 import BeautifulSoup

from yajuu.sources import SourceList, Source


def handle_link(url, *args, **kwargs):
    if not url.startswith('https'):
        url = 'https' + url[4:]

    download_1_payload = get_payload(
        requests.get(url).text, 'form'
    )

    download_2_payload = get_payload(
        requests.post(url, data=download_1_payload).text, 'form[name="F1"]'
    )

    soup = BeautifulSoup(
        requests.post(url, data=download_2_payload).text,
        'html.parser'
    )

    src = soup.select('.text-center a')[0].get('href')

    return SourceList([
        Source(src, *args, **kwargs)
    ])


def get_payload(source, selector):
    soup = BeautifulSoup(source, 'html.parser')
    form = soup.select(selector)

    fields = ['op', 'usr_login', 'id', 'fname', 'referer', 'method_free']

    payload = {}

    for input in soup.find_all('input'):
        if input.get('name') not in fields:
            continue

        payload[input.get('name')] = input.get('value')

    return payload
