from abc import ABC, abstractmethod

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

    def _as_soup(url, method='get', data=None, json=None, strip=False):
        '''Helper method to get an url as a beautifulsoup object.'''

        if method == 'post' or data or json:
            kwargs = {}

            if data:
                kwargs['data'] = data
            elif json:
                kwargs['json'] = json

            source = requests.post(url, **kwargs)
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
