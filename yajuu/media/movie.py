import datetime

from . import Media, TheTvDbMedia


class Movie(TheTvDbMedia, Media):
    def _update_metadata(self, query):
        show = self._get_result(query, self._select_result)

        self.metadata['id'] = show.id
        self.metadata['name'] = show.SeriesName
        self.year = show.FirstAired.year

    def list_files(self):
        return []

    def download(self):
        pass
