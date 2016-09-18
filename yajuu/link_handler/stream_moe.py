# https://stream.moe/dxhx3suwzdob

import re
import base64

import requests

from yajuu.sources import SourceList, Source


def handle_link(url, *args, **kwargs):
    html = requests.get(url).text

    frame_html = str(base64.b64decode(
        re.search(r'atob\(\'(.+)\'\)', html).group(1)
    ))

    src = re.search(r'<source src="(.+?)" type="', frame_html).group(1)

    return SourceList([
    	Source(src, *args, **kwargs)
    ])
