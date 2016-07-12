'''Provides an implementation of the season media format, which includes
seasons and episodes.'''

from abc import ABCMeta, abstractmethod
from glob import glob

from . import Media


class SeasonMedia(Media):

    '''Sub-abstract class, child of the Media class, which provides an
    implementation of the season mechanism.

    It supports multiple seasons, and implements an episode class.'''

    class Episode(metaclass=ABCMeta):

        '''To be used with the season media class.'''

        def __init__(self, season_number, number):
            self.number = number
            self.season_number = season_number
            self.metadata = {}
            self.binded = False
            self.file_path = None

        def _bind(self, media):
            self.binded = True
            self.media = media
            self._get_metadata()

        @abstractmethod
        def _get_metadata(self):
            pass

        def is_downloaded(self):
            pattern = self.file_path.format(ext='*')
            return len(glob(pattern)) > 0

    def __init__(self, query):
        self._seasons = {}
        super().__init__(query)

    def __iter__(self):
        return iter(self._seasons.items())

    @abstractmethod
    def get_file_path(self):
        '''Returns a string which defines where the files will be stored.'''
        pass

    def _add_season(self, number):
        if number in self._seasons:
            raise ValueError('Duplicate key {} found.'.format(number))

        self._seasons[number] = {}

    def get_seasons(self):
        return self._seasons

    def get_season(self, number):
        if number not in self._seasons:
            raise KeyError('The season {} was not found.'.format(
                number
            ))

        return self._seasons[number]

    def _add_episode(self, season_number, identifier, episode):
        if season_number not in self._seasons:
            raise KeyError('The season {} was not found.'.format(
                season_number
            ))

        if identifier in self._seasons[season_number]:
            raise ValueError('Duplicate key {} found in season {}'.format(
                identifier, season_number
            ))

        if not isinstance(episode, self.Episode):
            raise ValueError(
                'The passed episode is not an instance of the Episode class.'
            )

        self._seasons[season_number][identifier] = episode
        self._seasons[season_number][identifier]._bind(self)

    def get_episode(self, season_number, identifier):
        if season_number not in self._seasons:
            raise KeyError('The season {} was not found.'.format(
                season_number
            ))

        if identifier not in self._seasons[season_number]:
            raise KeyError(
                'The episode whose identifier is {} was not found in ' +
                'season {}.'.format(identifier, season_number)
            )

        return self._seasons[season_number][identifier]
