from .. import SeasonOrchestrator

from yajuu.extractors import (
	AnimeChibyExtractor, AnimeHavenExtractor, GogoAnimeIoExtractor,
	HtvanimeExtractor, KissAnimeExtractor
)


class AnimeOrchestrator(SeasonOrchestrator):
    def _get_query(self):
        return self.media.metadata['name']

    def _get_default_extractors(self):
    	return [KissAnimeExtractor]
        #return [
        #    AnimeChibyExtractor, AnimeHavenExtractor, GogoAnimeIoExtractor,
        #    HtvanimeExtractor
        #]
