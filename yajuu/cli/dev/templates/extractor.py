import concurrent.futures

from yajuu.extractors.anime.anime_extractor import AnimeExtractor
from yajuu.extractors.search_result import SearchResult{% if import_source %}
from yajuu.media.sources.source import Source{%endif%}{% if import_unshorten %}
from yajuu.extractors.unshorten import unshorten{% endif %}


class {{class_name}}(AnimeExtractor):

    def _get_url(self):
        return '{{url}}'

    def search(self):
        {% if disable_cloudflare %}self._disable_cloudflare()

        {% endif %}soup = self._post()

        return SearchResult.from_links(self.media, soup.find_all('a'))

    def extract(self, season, result):
        links = []

        with concurrent.futures.ThreadPoolExecutor(4) as executor:
            list(executor.map(self._worker, links))

    def _worker(self, link):
        self.logger.info('Processing episode {}'.format(episode_number))

        self.logger.info('Done processing episode {}'.format(episode_number))
