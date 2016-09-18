# https://docs.google.com/file/d/0B0ynmzIdQ-tCM1dKeWRaX0Nsc28/view

import re

import requests
import js2py

from yajuu.sources import Source, SourceList


def handle_link(url, *args, **kwargs):
    html = requests.get(url).text

    javascript = '{}.split(\'|\')[1]'.format(
        re.search(r'\["fmt_stream_map"\,(".+?")\]', html).group(1)
    )

    src = js2py.eval_js(javascript)

    return SourceList([
        Source(src, *args, **kwargs)
    ])
