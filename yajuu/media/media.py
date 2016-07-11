'''Provides the base implementation of the media class, that defines the core
behavior of all media.'''

from abc import ABCMeta, abstractmethod
import sys

import inquirer


class Media(metaclass=ABCMeta):

    '''Base abstract class for a media. It can be extended to implement for
    example the Movie or TV Show classes.

    The purpose for the class extending this one is to get data from the
    internet, just by passing a query. It should provide a seamless interface
    to get data in a clean way.'''

    class MediaNotFoundException(Exception):
        pass

    def __init__(self, query):
        self.metadata = {}
        self._update_metadata(query)
        self.metadata.update({'query': query})

    @abstractmethod
    def get_name(self):
        pass

    def _select_result(self, query, results):
        '''Provides a base implementation to select a result from a list.'''

        results = results[:10]

        question = inquirer.List(
            'name',
            message="Which title is correct for input '{}'?".format(
                query),
            choices=list(x[1] for x in results)
        )

        answers = inquirer.prompt([question])

        # If the user aborted
        if not answers:
            sys.exit(0)

        for result in results:
            if result[1] == answers['name']:
                return result[0]

        return None

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __ne__(self, other):
        pass

    @abstractmethod
    def _update_metadata(self, query):
        '''Returns a metadata dict from the query.'''

        pass

    @abstractmethod
    def list_files(self):
        '''Returns a list of all the downloaded files. The list can be a dict
        if needed.'''

        pass

    @abstractmethod
    def download(self):
        '''Downloads all the available sub-medias (episodes, tracks, ...).'''

        pass
