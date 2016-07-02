'''Each method there will try to extract download links from the designated
website, that includes the stream quality and direct source.
'''

import urllib.parse
import re
import subprocess
import base64

import shlex
import execjs
import requests
from bs4 import BeautifulSoup
import logging

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
        'tiwi.kiwi': unshorten_tiwi_kiwi,
        'www.solidfiles.com': unshorten_solidfiles,
        'vidstream.io': unshorten_vidstream,
        'solidfiles.com': unshorten_solidfiles,
        'mp4upload.com': unshorten_mp4upload,
        'stream.moe': unshorten_stream_moe,
        'bakavideo.tv': unshorten_bakavideo,
        'drive.google.com': unshorten_google_drive
    }

    host = urllib.parse.urlsplit(url).netloc

    logger.debug('Host is {}'.format(host))

    if host.startswith('www.'):
        logger.debug('Trimming "www."')
        host = host[4:]

    if host in unshorteners:
        logger.debug('Found method.')
        return unshorteners[host](url, quality)
    else:
        logger.warning('Could not unshorten {}'.format(url))

    return None


def get_quality(stream_url, quote=True):
    '''Using ffprobe, gets the given stream url quality.'''

    logger.debug('Getting quality of stream at {}'.format(stream_url))

    path = shlex.quote(stream_url) if quote else stream_url

    command = [
        'ffprobe', '-i', path, '-show_entries', 'stream=height', '-v', 'quiet',
        '-of', 'csv=p=0'
    ]

    logger.debug('Executing {}'.format(command))

    raw_output = subprocess.check_output(command)

    return int(''.join(x for x in raw_output.decode('utf-8') if x.isdigit()))


def unshorten_tiwi_kiwi(url, quality=None):
    # Some of the videos are available on the first page. If this regex is
    # successfull, then the video is directly available.
    quality_regex = re.compile(r'[0-9]+x([0-9]+), .+ [a-zA-Z]+')

    # On the download page, the download link does not use href, but calls some
    # javascript. After a short inspection of the code, I determined we only
    # need to extract the parameter of the called method to be able to generate
    # the link ourselves.
    onclick_regex = re.compile(
        r"download_video\('(.+)','(.+)','(.+)'\)"
    )

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
            quality_regex,
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
            onclick_regex,
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
            sources.append((quality, link))

            break

    return sources


def unshorten_solidfiles(url, quality=None):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')
    link = soup.find('a', {'id': 'download-btn'}).get('href')

    logger.debug('[solidfiles] Found {}'.format(link))

    returned = [(get_quality(link), link)]
    return returned


def unshorten_vidstream(url, quality=None):
    soup = BeautifulSoup(requests.get(url).text, 'html.parser')

    quality_regex = re.compile(r'Download \((\d+)P - .+')

    sources = []

    for link in soup.select('.mirror_link a'):
        sources.append((
            int(quality_regex.search(link.text).group(1)),
            link.get('href')
        ))

    logger.debug('[vidstream] found {} sources'.format(len(link)))

    return sources


def unshorten_mp4upload(url, quality=None):
    html = requests.get(url).text
    src_regex = re.compile(r'"file": "(.+)"')

    if 'File was deleted' in html:
        logger.warning('[mp4upload] File at {} was deleted'.format(url))
        return []

    src = src_regex.search(html).group(1)

    if quality is None:
        logger.warning('[mp4upload] quality was not passed')
        quality = get_quality(src)

    return [(quality, src)]


def unshorten_stream_moe(url, quality=None):
    base64_regex = re.compile(r'atob\(\'(.+)\'\)')
    src_regex = re.compile(r'<source src="(.+?)" type="')
    
    html = requests.get(url).text
    frame_html = str(base64.b64decode(base64_regex.search(html).group(1)))

    src = src_regex.search(frame_html).group(1)
    logger.debug('[stream.moe] found source {}'.format(src))

    if quality is None:
        logger.warning('[stream.moe] quality was not passed')
        quality = get_quality(src)

    return [(quality, src)]


def unshorten_bakavideo(url, quality=None):
    id_regex = re.compile(r'https?://bakavideo.tv/embed/(.+)')
    id = id_regex.search(url).group(1)

    data = requests.get(
        'https://bakavideo.tv/get/files.embed?f={}'.format(id)
    ).json()

    html = base64.b64decode(
        data['content']
    ).decode('utf-8').replace('\n', '').replace('\t', '')

    soup = BeautifulSoup(html, 'html.parser')
    source_div = src = soup.find('source')

    if not source_div:
        return None

    src = source_div.get('src')

    logger.debug('[bakavideo] found source {}'.format(src))

    if quality is None:
        logger.warning('[bakavideo] quality was not passed')
        quality = get_quality(src)

    return [(quality, src)]


def unshorten_google_drive(url, quality=None):
    html = requests.get(url).text
    fmt_stream_map_regex = re.compile(r'\["fmt_stream_map"\,(".+?")\]')

    javascript = '{}.split(\'|\')[1]'.format(
        fmt_stream_map_regex.search(html).group(1)
    )

    logger.debug('Executing: {}'.format(javascript))

    src = execjs.eval(javascript)

    logger.debug('[google drive] found source {}'.format(src))

    if quality is None:
        logger.warning('[google drive] quality was not passed')
        quality = get_quality(src)

    return [(quality, src)]
