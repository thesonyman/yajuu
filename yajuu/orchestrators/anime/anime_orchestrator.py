from yajuu.orchestrators import SeasonOrchestrator

from yajuu.extractors import (
    MasteraniExtractor, RawrAnimeExtractor, HtvanimeExtractor,
    MoeTubeExtractor, AnimeChibyExtractor, AnimeHavenExtractor,
    GogoAnimeIoExtractor, KissAnimeExtractor, ChiaAnimeCoExtractor,
    AnilinktzExtractor
)


class AnimeOrchestrator(SeasonOrchestrator):

    def _get_query(self):
        return self.media.metadata['name']

    def _get_default_extractors(self):
        return [
            AnimeChibyExtractor, AnimeHavenExtractor, GogoAnimeIoExtractor,
            HtvanimeExtractor, MasteraniExtractor, RawrAnimeExtractor,
            MoeTubeExtractor, KissAnimeExtractor, ChiaAnimeCoExtractor,
            AnilinktzExtractor
        ]
