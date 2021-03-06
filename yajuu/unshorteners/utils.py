import logging
import subprocess

from yajuu.config import config

logger = logging.getLogger(__name__)


def get_quality(stream_url):
    '''Using ffprobe, gets the given stream url quality.'''

    logger.debug('Getting quality of stream at {}'.format(stream_url))

    command = [
        'ffprobe', '-i', stream_url, '-show_entries', 'stream=height', '-v',
        'quiet', '-of', 'csv=p=0'
    ]

    logger.debug('Executing {}'.format(command))

    retries = 0
    raw_output = None

    while retries < 5:
        try:
            raw_output = subprocess.check_output(
                command, timeout=config['misc']['ffprobe_timeout']
            )
            break
        except subprocess.CalledProcessError as e:
            logger.error(e)
            retries += 1

    if not raw_output:
        return 0

    return int(''.join(x for x in raw_output.decode('utf-8') if x.isdigit()))
