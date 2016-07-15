import re
import time
import random
import urllib.parse

from . import MovieExtractor
from .. import unshorten


class IceFilmsExtractor(MovieExtractor):

    def _get_url(self):
        return 'http://www.icefilms.info'

    def search(self):
        soup = self._get('http://www.icefilms.info/search.php', params={
            'q': self.media.metadata['name'],
            'x': 0,
            'y': 0
        })

        results = []

        for result in soup.select('.title a'):
            results.append((result.text, result.get('href')))

        return results

    def extract(self, result):
        soup = self._get(self._get_url() + result[1])

        sources_soup = self._get(
            self._get_url() + soup.select('iframe#videoframe')[0].get('src')
        )

        referer = self._get_url() + \
            soup.select('iframe#videoframe')[0].get('src')

        for quality_div in sources_soup.select('.ripdiv'):
            print('=> ' + quality_div.find('b').text)

            t = re.search('t=(\d+?)"', sources_soup.prettify()).group(1)
            results = re.search(
                'var s=(\d+?),m=(\d+?);', sources_soup.prettify())
            s, m = results.group(1), results.group(2)
            sec = re.search(
                'f.lastChild.value="(.+?)"', sources_soup.prettify()).group(1)

            for source in quality_div.select('a[onclick]'):
                id = source.get('onclick')[3:-1]

                success = False

                while not success:
                    source_url = self._get_url() + (
                        '/membersonly/components/com_iceplayer/video.'
                        'phpAjaxResp.php?s={}&t={}'
                    ).format(id, t)

                    payload = {
                        'id': id,
                        's': str(random.randint(10000, 10060)),
                        'iqs': '',
                        'url': '',
                        'm': str(random.randint(10000, 10500)),
                        'cap': ' ',
                        'sec': sec,
                        't': t
                    }

                    headers = {
                        'Referer': referer
                    }

                    response, soup = self._post(
                        source_url, data=payload, return_response=True,
                        headers=headers
                    )

                    if len(response.text) > 0:
                        success = True
                    else:
                        time.sleep(random.randint(1, 3))

                # The url is something like 'blah?url=some_url?url=the url'.
                encoded_sub_url = urllib.parse.parse_qsl(
                    urllib.parse.urlparse(response.text).query
                )[0][1]  # First item, then value

                host_url = urllib.parse.parse_qsl(
                    urllib.parse.urlparse(encoded_sub_url).query
                )[0][1]

                try:
                    self.sources.add_sources(unshorten(host_url))
                except:
                    pass

                time.sleep(0.5)
