from abc import ABCMeta, abstractmethod
import urllib.parse
import logging
import coloredlogs
import sys

import requests
import cfscrape
from bs4 import BeautifulSoup

from yajuu.media import SourceList


class abstractstatic(staticmethod):
    __slots__ = ()

    def __init__(self, function):
        super(abstractstatic, self).__init__(function)
        function.__isabstractmethod__ = True

    __isabstractmethod__ = True


class Extractor(metaclass=ABCMeta):

    def __init__(self, media):
        self.session = cfscrape.create_scraper()
        self.media = media
        self.links = []
        self.sources = SourceList()

        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

        formatter = logging.Formatter(
            '%(levelname)s - \033[92m{}\033[0m: %(message)s'.format(
                self.__class__.__name__
            )
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        # Prevent the messages from being propagated to the root logger
        self.logger.propagate = 0

        self.logger.addHandler(handler)
        coloredlogs.install(level='DEBUG')

    @abstractstatic
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
