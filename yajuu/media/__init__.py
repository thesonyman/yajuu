'''Provides all the different media implementation. Use this package to either
get or save data.'''

from .sources import *
from .providers import *
from .media import Media
from .season_media import SeasonMedia
from .anime import Anime
from .movie import Movie

from ..orchestrators import AnimeOrchestrator, MovieOrchestrator

MEDIA_TYPES = {
    'anime': (Anime, AnimeOrchestrator),
    'movie': (Movie, MovieOrchestrator)
}
