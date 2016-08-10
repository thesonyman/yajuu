"""Provides the implementation of the season media class."""

import os

from yajuu.config import config
from yajuu.media.media import Media
from yajuu.cli.media.download.downloader import download_file


class SeasonMedia(Media):

    """Abstract class for a season media.

    It should represent a media with seasons, such as tv shows or animes.

    """

    def download(self, sources, dump=False):
        media_config = self.get_path_config()
        base_path = os.path.join(config['paths']['base'], media_config['base'])

        mode = 'Dumping' if dump else 'Downloading'

        for season, season_sources in sources.items():
            season_path = os.path.join(
                base_path,
                self.metadata['name'],
                media_config['season'].format(season_number=season)
            )

            self.logger.info('%s season %i', mode, season)

            for episode_number, sources in season_sources.items():
                episode_count = len(self.metadata['seasons'][season])

                self.logger.info(
                    '%s episode %i/%i of season %i', mode, episode_number,
                    episode_count, season
                )

                path_params = {
                    'anime_name': self.metadata['name'],
                    'season_number': season,
                    'episode_number': episode_number
                }

                download_file(
                    dump, self, media_config['episode'], path_params, sources,
                    directory=season_path
                )
