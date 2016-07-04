import logging

logger = logging.getLogger(__name__)


def download_single_media(media, orchestrator):
    sources = get_sources(media, orchestrator)

def download_season_media(media, season, orchestrator):
    sources = get_sources(media, orchestrator)

def get_sources(media, orchestrator):
    logger.info('-> Starting downloads for media {}'.format(
        media.metadata['name']
    ))

    logger.info('Starting the extract phase')

    return orchestrator.extract()
