from abc import ABCMeta, abstractmethod
import urllib.parse

import requests
from bs4 import BeautifulSoup


class Extractor(metaclass=ABCMeta):
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
        cookies=None, strip=False, headers=None
    ):
        '''Helper method to get an url as a beautifulsoup object.'''

        if params:
            url = url.format(params=urllib.parse.urlencode(params))

        kwargs = {}

        if cookies:
            kwargs['cookies'] = cookies

        if headers:
            kwargs['headers'] = headers

        if method == 'post' or data or json:
            if data:
                kwargs['data'] = data
            elif json:
                kwargs['json'] = json

            if self.session:
                source = self.session.post(url, **kwargs).text
            else:
                source = requests.post(url, **kwargs).text
        elif method == 'get':
            if self.session:
                source = self.session.get(url, **kwargs).text
            else:
                source = requests.get(url, **kwargs).text
        else:
            raise ValueError('The method must be either get or post.')

        if strip:
            source = (
                source.replace('\\n', '')
                .replace('\\t', '')
                .replace('\\', '')
            )

        return BeautifulSoup(source, 'html.parser')
