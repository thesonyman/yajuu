import importlib
import logging
import pprint

from yajuu.media.types import MEDIA_TYPES
from yajuu.extractors.season_extractor import SeasonExtractor
from yajuu.unshorteners import unshorten

logger = logging.getLogger(__name__)


def run_extractor(media, media_type, file_name, class_name, index):
    logger.info('Loading the extractor..')

    module = importlib.import_module('yajuu.extractors.{}.{}'.format(
        media_type, file_name
    ))

    extractor_cls = getattr(module, class_name)

    if issubclass(extractor_cls, SeasonExtractor):
        episodes = list(media.metadata['seasons'][
            list(media.metadata['seasons'])[0]
        ].keys())

        extractor = extractor_cls(media, 1, (min(episodes), max(episodes)))
    else:
        extractor = extractor_cls(media)

    logger.info('Searching..')
    results = extractor.search()
    logger.info(pprint.pformat(results, indent=4))

    if index is None:
        logger.info('No index was passed. Pass one to continue.')
        return

    result = results[index]

    logger.info('Extracting')

    if issubclass(extractor_cls, SeasonExtractor):
        extractor.extract(1, result.identifier)
    else:
        extractor.extract(result.identifier)

    logger.info(pprint.pformat(extractor.sources, indent=4))


def run_unshortener(url, quality):
    sources = unshorten(url, quality=quality)
    pprint.pprint(sources, indent=4)
