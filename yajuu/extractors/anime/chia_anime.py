import re
import concurrent.futures

import requests

from . import AnimeExtractor


class ChiaAnimeExtractor(AnimeExtractor):
	def _get_url(self):
		return 'http://m.chia-anime.tv'

	def search(self):
		soup = self._get('http://m.chia-anime.tv/catlist.php', data={
			'tags': self.media.metadata['name']
		})

		results = []

		for link in soup.select('div.title > a'):
			results.append((
				link.text,
				('http://m.chia-anime.tv' + link.get('href'))
			))

		return results

	def extract(self, season, result):
		soup = self._get(result[1])
		episodes_select = soup.find('select', {'id': 'id'})

		base_url = 'http://m.chia-anime.tv/mw.php?id={}&submit=Watch'

		episodes = []
		number_regex = re.compile(r'^Select .+? Episode (\d+)$')

		for option in episodes_select.find_all('option'):
			url = base_url.format(option.get('value'))

			number_regex_result = number_regex.search(option.text.strip())

			if not number_regex_result:
				self.logger.warning('Episode at url {} is invalid'.format(
					url
				))

				continue

			episodes.append((
				int(number_regex_result.group(1)),
				url
			))

			self.logger.debug(base_url.format(option.get('value')))

		sources = {}

		with concurrent.futures.ThreadPoolExecutor(16) as executor:
			for data in executor.map(self._page_worker, episodes):
				if not data:
					continue

				data = episode_number, episode_sources

				if episode_number not in sources:
					sources[episode_number] = []

				sources[episode_number]+= episode_sources

		import pprint
		pprint.pprint(sources)
		import sys
		sys.exit(0)
		return sources

	def _page_worker(self, data):
		episode_number, url = data

		self.logger.info('Processing episode {}'.format(episode_number))

		soup = self._get(url)

		self.logger.info('Done processing episode {}'.format(episode_number))
		return []