from yajuu.orchestrators.season_orchestrator import SeasonOrchestrator

from yajuu.extractors.anime.masterani import MasteraniExtractor
from yajuu.extractors.anime.rawr_anime import RawrAnimeExtractor
from yajuu.extractors.anime.htvanime import HtvanimeExtractor
from yajuu.extractors.anime.moetube import MoeTubeExtractor
from yajuu.extractors.anime.anime_chiby import AnimeChibyExtractor
from yajuu.extractors.anime.anime_haven import AnimeHavenExtractor
from yajuu.extractors.anime.gogoanime_io import GogoAnimeIoExtractor
from yajuu.extractors.anime.kissanime import KissAnimeExtractor
from yajuu.extractors.anime.chia_anime_co import ChiaAnimeCoExtractor
from yajuu.extractors.anime.anilinktz import AnilinktzExtractor
from yajuu.extractors.anime.animefrost import AnimeFrostExtractor


class AnimeOrchestrator(SeasonOrchestrator):

    def _get_query(self):
        return self.media.metadata['name']

    def _get_default_extractors(self):
        return [
            AnimeChibyExtractor, AnimeHavenExtractor, GogoAnimeIoExtractor,
            HtvanimeExtractor, MasteraniExtractor, RawrAnimeExtractor,
            MoeTubeExtractor, KissAnimeExtractor, AnimeFrostExtractor
        ]
