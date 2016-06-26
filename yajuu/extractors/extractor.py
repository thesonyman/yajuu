from abc import ABCMeta, abstractmethod
import urllib.parse

import requests
import cfscrape
from bs4 import BeautifulSoup


class Extractor(metaclass=ABCMeta):
    def __init__(self, media):
        self.session = cfscrape.create_scraper()
        self.media = media
        self.links = []

    @abstractmethod
    def _get_url(self):
        pass

    @abstractmethod
    def search(self):
        pass

    @abstractmethod
    def extract(self, result):
        pass

    def _as_soup(self, *args, fn='get', return_response=False, **kwargs):
        '''Small helper to get beautifulsoup objects easilly. The passed
        arguments except fn and return_response will be passed to the requests
        method call.'''

        if hasattr(self, 'session'):
            request_object = self.session
        else:
            request_object = requests

        response = getattr(request_object, fn)(*args, **kwargs)
        soup = BeautifulSoup(response.text, 'html.parser')

        if return_response:
            return (response, soup)
        else:
            return soup

    def _disable_cloudflare(self):
        '''Initiate a request to the main page before calling anything else.'''
        self.session.get(self._get_url())

    def _get(self, *args, **kwargs):
        return self._as_soup(*args, fn='get', **kwargs)

    def _post(self, *args, **kwargs):
        return self._as_soup(*args, fn='post', **kwargs)

    def __as_soup(
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

            if hasattr(self, 'session'):
                source = self.session.post(url, **kwargs).text
            else:
                source = requests.post(url, **kwargs).text
        elif method == 'get':
            if hasattr(self, 'session'):
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
