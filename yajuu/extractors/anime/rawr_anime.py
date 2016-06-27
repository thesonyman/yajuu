import concurrent.futures

import requests
from bs4 import BeautifulSoup

from . import AnimeExtractor
from .. import unshorten


class RawrAnimeExtractor(AnimeExtractor):
	def _get_url(self):
		return 'http://rawranime.tv'

	def search(self):
		html = requests.get('http://rawranime.tv/index.php', params={
			'ajax': 'anime',
			'do': 'search',
			's': self.media.metadata['name']
		}).text.replace('\\', '')

		soup = BeautifulSoup(html, 'html.parser')

		results = []

		for link in soup.find_all('a'):
			title = link.find('div', {'class': 'quicksearch-title'}).text
			id = link.get('href')  # With a leading slash

			results += [
				(title + ' (Sub)', id), (title + ' (Dub)', id)
			]

		return results

	def extract(self, season, result):
		version = 'subbed' if result[0].endswith(' (Sub)') else 'dubbed'
		url = 'http://rawranime.tv' + result[1] + '?apl=1'

		html = requests.get(url).json()['html']
		soup = BeautifulSoup(html, 'html.parser')

		episodes = []

		for episode in soup.find_all('div', {'class': 'ep '}):
			number_div = episode.find('div', {'class': 'ep-number'})
			episodes.append((version, result[1], number_div.text))

		sources = {}

		with concurrent.futures.ThreadPoolExecutor(16) as executor:
			for number, _sources in executor.map(self.page_worker, episodes):
				if number not in sources:
					sources[number] = []

				sources[number] += _sources

		return sources

	def page_worker(self, data):
		version, id, number = data

		print('[RawrAnime] Processing episode {}'.format(number))

		id = id[7:]  # Remove '/anime'

		url = 'http://rawranime.tv/watch/{}/episode-{}'.format(id, number)
		soup = self._get(url)

		elements = soup.find_all(
			lambda x: x.name == 'div' and x.has_attr('data-src') and
			x.has_attr('data-quality')
		)

		sources = []

		for element in elements:
			if element.get('data-lang') != version:
				continue

			quality = int(''.join(
				x for x in element.get('data-quality') if x.isdigit()
			))

			src = unshorten(element.get('data-src'), quality=quality)

			if src is None:
				continue

			sources += src

		print('[RawrAnime] Done processing episode {}'.format(number))

		return (int(number), sources)
