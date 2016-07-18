'''Provides all the different media implementation. Use this package to either
get or save data.'''

from yajuu.media.sources import *
from yajuu.media.providers import *
from yajuu.media.media import Media
from yajuu.media.season_media import SeasonMedia
from yajuu.media.anime import Anime
from yajuu.media.movie import Movie

from yajuu.orchestrators import AnimeOrchestrator, MovieOrchestrator

MEDIA_TYPES = {
    'anime': (Anime, AnimeOrchestrator),
    'movie': (Movie, MovieOrchestrator)
}
