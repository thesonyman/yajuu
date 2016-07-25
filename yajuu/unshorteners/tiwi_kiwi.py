import re
import logging

import requests
from bs4 import BeautifulSoup

from yajuu.media.sources.source import Source

logger = logging.getLogger(__name__)


def unshorten(url, quality=None):
    # Some of the videos are available on the first page. If this regex is
    # successfull, then the video is directly available.

    # On the download page, the download link does not use href, but calls some
    # javascript. After a short inspection of the code, I determined we only
    # need to extract the parameter of the called method to be able to generate
    # the link ourselves.

    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    # Lists all the download links
    download_table = soup.find('table', {'class': 'tbl1'})

    if not download_table:
        logger.warning('[tiwi.kiwi] could not locate download table')
        return None

    sources = []

    for tr in download_table.find_all('tr'):
        # We filter out the first row (header) like that, since there are no
        # thead or tbody.
        if len(tr.find_all('a')) <= 0:
            continue

        # First get the quality
        quality_regex_results = re.search(
            r'[0-9]+x([0-9]+), .+ [a-zA-Z]+',
            tr.find_all('td')[1].text
        )

        if not quality_regex_results:
            continue

        quality = int(quality_regex_results.group(1))

        logger.debug('[tiwi.kiwi] found link with quality {}'.format(
            quality
        ))

        # Then extract the download url
        onclick_regex_result = re.search(
            r"download_video\('(.+)','(.+)','(.+)'\)",
            tr.find('a').get('onclick')
        )

        if not onclick_regex_result:
            continue

        code = onclick_regex_result.group(1)
        mode = onclick_regex_result.group(2)
        hash = onclick_regex_result.group(3)

        logger.debug('[tiwi.kiwi] {}'.format({
            'code': code, 'mode': mode, 'hash': hash
        }))

        url = (
            'http://tiwi.kiwi/dl?op=download_orig&id={}&'
            'mode={}&hash={}'.format(code, mode, hash)
        )

        # The website often returns an unauthorized error, that we can bypass
        # by sending more requests. Usually, only one or two requests are
        # needed.
        retries = 10
        retry = 0

        while retry < retries:
            download_soup = BeautifulSoup(
                requests.get(url).text, 'html.parser'
            )

            # The container is always present. However, the span isn't when a
            # security error occur.
            span = download_soup.find('div', {'id': 'container'}).find('span')

            if not span:
                logger.warning('[tiwi.kiwi] Retrying, {} left'.format(retry))
                retry += 1
                continue

            link = span.find('a').get('href')
            logger.debug('[tiwi.kiwi] Found link: {}'.format(link))
            sources.append(Source(link, quality))

            break

    return sources
