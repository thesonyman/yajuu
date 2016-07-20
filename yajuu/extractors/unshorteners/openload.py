import logging
import re

import requests

from . import get_quality
from .aa import AADecoder
from yajuu.media import Source

logger = logging.getLogger(__name__)


def unshorten_openload(url, quality=None):
    '''Inspired from https://github.com/Zanzibar82/plugin.video.streamondemand/
    blob/bf655c445e77be57ef4ece84f11b5899a41e0939/servers/openload.py.'''

    import js2py

    html = requests.get(url).text

    # Extract the obfuscated code from which we can deduce the url
    matches = re.findall(r'(ﾟωﾟﾉ= /｀ｍ´）ﾉ ~┻━┻.+?)</script>', html)
    matches = [AADecoder(m).decode() for m in matches]
    logger.debug(matches)

    # Search the index (the page have two urls, we need to select the correct
    # one).
    js = re.search(r'window.+[\n\s]?.+= (.+?);', matches[0]).group(1)
    index = js2py.eval_js(js)
    logger.debug(index)

    # Now we get the valid url
    section = matches[index]
    function = re.search(r'window.+\[\d\]=(\(.+\));window', section).group(1)
    url = conv(function)
    logger.debug(matches)

    if quality is None:
        quality = get_quality(url)

    return [Source(url, quality)]


def conv(s, addfactor=None):
    '''Converts the found javascript function to a valid url.'''

    if 'function()' in s:
        addfactor = s.split('b.toString(')[1].split(')')[0]
        fname = re.findall('function\(\)\{function (.*?)\(', s)[0]
        s = s.replace(fname, 'myfunc')
        s = ''.join(s.split('}')[1:])

    if '+' not in s:
        if '.0.toString' in s:
            ival, b = s.split('.0.toString(')
            b = b.replace(')', '')
            return baseN(int(ival), int(eval(b)))
        elif 'myfunc' in s:
            b, ival = s.split('myfunc(')[1].split(',')
            ival = ival.replace(')', '').replace('(', '')
            b = b.replace(')', '').replace('(', '')
            b = eval(addfactor.replace('a', b))
            return baseN(int(ival), int(b))
        else:
            return eval(s)

    r = ''

    for ss in s.split('+'):
        r += conv(ss, addfactor)

    return r


def baseN(num, b, numerals='0123456789abcdefghijklmnopqrstuvwxyz'):
    return (
        (num == 0) and numerals[0]
    ) or (
        baseN(num // b, b, numerals).lstrip(numerals[0]) + numerals[num % b]
    )
