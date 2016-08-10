'''Provides the implementation of the anime class.'''

from yajuu.media.season_media import SeasonMedia
from yajuu.media.providers.thetvdb import TheTvDbProvider
from yajuu.config import config


class Anime(TheTvDbProvider, SeasonMedia):

    """Media class the defines an anime.

    Currently fetches data using the tvdb provider.
    
    """

    def get_path_config(self):
        return config['path']['medias']['anime']

    def _update_metadata(self):
        show = self._get_result(self.query, self._select_result)

        self.metadata = {}
        self.metadata['id'] = show.id
        self.metadata['name'] = show.SeriesName
        self.metadata['seasons'] = {}

        for season in show:
            self.metadata['seasons'][season.season_number] = {}

            for episode in season:
                episode = {
                    'number': episode.EpisodeNumber,
                    'name': episode.EpisodeName
                }
