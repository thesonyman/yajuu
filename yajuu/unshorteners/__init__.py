import urllib.parse
import logging
import importlib

logger = logging.getLogger(__name__ + '.' + 'unshorten')

formatter = logging.Formatter('%(levelname)s: [UNSHORTEN] %(message)s')

handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Prevent the messages from being propagated to the root logger
logger.propagate = 0

logger.addHandler(handler)


def unshorten(url, quality=None):
    '''Will try to locate the correct unshortener by itself.'''

    unshorteners = {
        'tiwi.kiwi': 'tiwi_kiwi',
        'www.solidfiles.com': 'solidfiles',
        'vidstream.io': 'vidstream',
        'mp4upload.com': 'mp4upload',
        'stream.moe': 'stream_moe',
        'bakavideo.tv': 'bakavideo',
        'drive.google.com': 'google_drive',
        'tusfiles.net': 'tusfiles',
        'upload.af': 'upload_af',
        'openload.co': 'openload',
        'playbb.me': 'playbb',
        'videonest.net': 'videonest'
    }

    host = urllib.parse.urlsplit(url).netloc

    logger.debug('Host is {}'.format(host))

    if host.startswith('www.'):
        logger.debug('Trimming "www."')
        host = host[4:]

    if host in unshorteners:
        logger.debug('Found method.')

        return importlib.import_module(
            'yajuu.unshorteners.' + unshorteners[host]
        ).unshorten(url, quality)
    else:
        logger.warning('Could not unshorten {}'.format(url))

    return None
