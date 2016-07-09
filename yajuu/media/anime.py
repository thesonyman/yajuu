'''Provides the implementation of the anime class.'''

import os

from pytvdbapi import api
from pytvdbapi.error import TVDBIndexError

from . import SeasonMedia, TheTvDbProvider
from yajuu.config import config


class Anime(TheTvDbProvider, SeasonMedia):

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

    def get_name(self):
        return 'Anime'

    def _update_metadata(self, query):
        show = self._get_result(query, self._select_result)

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
