from yajuu.media.anime import Anime
from yajuu.media.movie import Movie
from yajuu.orchestrators.anime_orchestrator import AnimeOrchestrator
from yajuu.orchestrators.movie_orchestrator import MovieOrchestrator

MEDIA_TYPES = {
    'anime': (Anime, AnimeOrchestrator),
    'movie': (Movie, MovieOrchestrator)
}
