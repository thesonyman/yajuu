# http://www.solidfiles.com/d/2f6268f610/

import re

import requests
from bs4 import BeautifulSoup

from yajuu.sources import SourceList, Source


def handle_link(url, *args, **kwargs):
    identifier = re.search(
        r'^https?:\/\/(?:www)?.solidfiles.com\/d\/(.+?)(?:\/dl)?\/?$',
        url
    ).group(1)

    url = 'http://www.solidfiles.com/v/{}'.format(identifier)
    session = requests.Session()  # To persist the cookies

    # First, get the csrf token
    soup = BeautifulSoup(session.get(url).text, 'html.parser')
    token = soup.find('input', {'name': 'csrfmiddlewaretoken'}).get('value')

    # Then get to the download page and get the link
    html = session.post(url + '/dl', data={'csrfmiddlewaretoken': token}).text
    soup = BeautifulSoup(html, 'html.parser')
    src = soup.find('a', text=re.compile('click here')).get('href')

    return SourceList([
        Source(src, *args, **kwargs)
    ])
