from yajuu.orchestrators.orchestrator import Orchestrator
from yajuu.extractors.movie.icefilms import IceFilmsExtractor


class MovieOrchestrator(Orchestrator):

    def _get_query(self):
        return self.media.metadata['name']

    def _get_default_extractors(self):
        return [IceFilmsExtractor]
