'''Provides the implementation of the anime class.'''

import os

from pytvdbapi import api
from pytvdbapi.error import TVDBIndexError

from .season_media import SeasonMedia
from yajuu.config import config


class Anime(SeasonMedia):
    _db = None

    class Episode(SeasonMedia.Episode):
        def __init__(self, season_number, data):
            super().__init__(season_number, data.EpisodeNumber)
            self._data = data

        def _get_metadata(self):
            self.metadata['name'] = self._data.EpisodeName

            self.file_path = self.media.get_file_path().format(
                anime_name=self.media.metadata['name'],
                season_number=self.season_number,
                episode_number=self.number,
                ext='{ext}',
                **self.metadata
            )

    def __init__(self, query):
        if Anime._db is None:
            Anime._db = api.TVDB(config['thetvdb']['api_key'])

        super().__init__(query)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__) and
            self.metadata['id'] == other.metadata['id']
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def _update_metadata(self, query):
        # First, fetch the show itself

        not_found_exception = self.MediaNotFoundException(
            'Could not find the anime on thetvdb.'
        )

        try:
            results = Anime._db.search(query, config['thetvdb']['language'])

            if len(results) == 0:
                raise not_found_exception
            elif len(results) == 1:
                show = results[0]
            else:
                show = None

                print('Search results for {} :'.format(query))

                for index, result in enumerate(results):
                    print('{} - {}'.format(index, result.SeriesName))

                print('Please select the correct result.')

                while not show:
                    index = input('>> ')

                    try:
                        index = int(index)
                        show = results[index]
                    except (ValueError, IndexError):
                        pass

            # Fetch the metadata
            show.update()
        except TVDBIndexError:
            raise not_found_exception

        # Now we can extract the wanted data

        self.metadata = {}
        self.metadata['id'] = show.id
        self.metadata['name'] = show.SeriesName

        for season in show:
            self._add_season(season.season_number)

            for episode in season:
                self._add_episode(
                    season.season_number, episode.EpisodeNumber,
                    self.Episode(season.season_number, episode)
                )

    def get_file_path(self):
        path = os.path.join(
            config['paths']['base'],
            config['paths']['medias']['anime']['base'],
            self.metadata['name'],
            config['paths']['medias']['anime']['season'],
            config['paths']['medias']['anime']['episode']
        )

        return path

    def list_files(self):
        return []

    def download(self):
        pass
