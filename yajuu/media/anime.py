'''Provides the implementation of the anime class.'''

from pytvdbapi import api
from pytvdbapi.error import TVDBIndexError

from .season_media import SeasonMedia
from yajuu.config import config


class Anime(SeasonMedia):
    _db = None

    class Episode(SeasonMedia.Episode):
        def _get_metadata(self):
            pass

    def __init__(self, query):
        if Anime._db is None:
            Anime._db = api.TVDB(config['thetvdb']['api_key'])

        super().__init__(query)

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
        self.metadata['title'] = show.SeriesName

        for season in show:
            self._add_season(season.season_number)

            for episode in season:
                self.Episode(episode.EpisodeNumber)

                self._add_episode(
                    season.season_number, episode.EpisodeNumber,
                    self.Episode(episode.EpisodeNumber)
                )

    def get_file_path(self):
        return 's{season_number}E{episode_number}.{ext}'

    def list_files(self):
        return []

    def download(self):
        pass
