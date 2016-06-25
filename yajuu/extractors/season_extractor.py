from . import Extractor


class SeasonExtractor(Extractor):
    def __init__(self, media, season):
        super().__init__(media)
        self.seasons = {}
        self.season = season
