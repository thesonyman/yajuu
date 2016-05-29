'''Provides the base implementation of the media class, that defines the core
behavior of all media.'''

from abc import ABC, abstractmethod


class Media(ABC):
    class MediaNotFoundException(Exception):
        pass

    def __init__(self, query):
        self.metadata = {}
        self._update_metadata(query)
        self.metadata.update({'query': query})

    @abstractmethod
    def _update_metadata(self, query):
        """Returns a metadata dict from the query."""

        pass

    @abstractmethod
    def list_files(self):
        """Returns a list of all the downloaded files. The list can be a dict
        if needed."""

        pass

    @abstractmethod
    def download(self):
        """Downloads all the available sub-medias (episodes, tracks, ...)."""

        pass
