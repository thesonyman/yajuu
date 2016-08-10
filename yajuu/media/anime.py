'''Provides the implementation of the anime class.'''

from yajuu.media.season_media import SeasonMedia
from yajuu.media.providers.thetvdb import TheTvDbProvider
from yajuu.config import config


class Anime(TheTvDbProvider, SeasonMedia):

    """Media class the defines an anime.

    Currently fetches data using the tvdb provider.
    
    """

    def get_path_config(self):
        return config['paths']['medias']['anime']

    def _update_metadata(self):
        show = self._get_result(self.query, self._select_result)

        self.metadata = {}
        self.metadata['id'] = show.id
        self.metadata['name'] = show.SeriesName
        self.metadata['seasons'] = {}

        for season in show:
            season_data = {}

            for episode in season:
                episode_data = {
                    'number': episode.EpisodeNumber,
                    'name': episode.EpisodeName
                }

                season_data[episode.EpisodeNumber] = episode_data

            self.metadata['seasons'][season.season_number] = season_data
