'''Provides binding from the media class to the orchestrator class.'''

from yajuu.media.anime import Anime
from yajuu.media.movie import Movie
from yajuu.orchestrators.anime_orchestrator import AnimeOrchestrator
from yajuu.orchestrators.movie_orchestrator import MovieOrchestrator


# The keys here should be the same as in the config
MEDIA_TYPES = {
    'anime': (Anime, AnimeOrchestrator),
    'movie': (Movie, MovieOrchestrator)
}
