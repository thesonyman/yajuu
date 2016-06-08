from abc import ABC, abstractmethod
import urllib.parse

import requests
from bs4 import BeautifulSoup


class Extractor(ABC):
    def __init__(self, media):
        self.media = media
        self.links = []

    @abstractmethod
    def search(self):
        pass

    @abstractmethod
    def extract(self, result):
        pass

    def _as_soup(
        self, url, method='get', params=None, data=None, json=None,
        strip=False
    ):
        '''Helper method to get an url as a beautifulsoup object.'''

        if params:
            url = url.format(params=urllib.parse.urlencode(params))

        if method == 'post' or data or json:
            kwargs = {}

            if data:
                kwargs['data'] = data
            elif json:
                kwargs['json'] = json

            source = requests.post(url, **kwargs).text
        elif method == 'get':
            source = requests.get(url).text
        else:
            raise ValueError('The method must be either get or post.')

        if strip:
            source = (
                source.replace('\\n', '')
                .replace('\\t', '')
                .replace('\\', '')
            )

        return BeautifulSoup(source, 'html.parser')
