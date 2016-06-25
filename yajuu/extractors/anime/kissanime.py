import re
import time
import base64
import concurrent.futures

import cfscrape
import requests
import bs4
import execjs

from . import AnimeExtractor


class KissAnimeExtractor(AnimeExtractor):
	EPISODE_REGEX = re.compile('.+ Episode (\d{3,})')

	QUALITY_REGEX = re.compile('(\d{3,})p')

	def __init__(self, media, season):
		super().__init__(media, season)

		self.session = cfscrape.create_scraper()
		self.session.headers['User-Agent'] = (
			'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like '
			'Gecko) Chrome/41.0.2228.0 Safari/537.36'
		)

	def search(self):
		# Preliminary, else kissanime returns 404
		self.session.get('https://kissanime.to')

		soup = self._as_soup(
			'https://kissanime.to/Search/SearchSuggest',
			method='post', data={
				'type': 'Anime',
				'keyword': self.media.metadata['name']
			},
			headers={
				'origin': 'https://kissanime.to',
				'referer': 'https://kissanime.to',
				'x-requested-with': 'XMLHttpRequest'
			}
		)

		results = []

		for link in soup.find_all('a'):
			results.append((link.text, link.get('href')))

		return results

	def extract(self, season, result):
		soup = self._as_soup(result[1], method='get')

		sources = {}

		links = soup.select('table a[href^="/Anime/"]')

		with concurrent.futures.ThreadPoolExecutor(16) as executor:
			for returned in executor.map(
				self.episode_worker,
				soup.select('table a[href^="/Anime/"]')
			):
				if not returned:
					continue

				episode_number, extractor_sources = returned

				if episode_number not in sources:
					sources[episode_number] = []

				sources[episode_number] += extractor_sources

		return sources

	def episode_worker(self, link):
		url = 'https://kissanime.to' + link.get('href')
		episode_number_results = self.EPISODE_REGEX.search(link.text)

		if not episode_number_results:
			return None

		episode_number = int(episode_number_results.group(1))

		print('[KissAnime] Processing episode {}'.format(episode_number))

		episode_response = self.session.get(url)
		episode_soup = bs4.BeautifulSoup(episode_response, 'html.parser')

		quality_select = episode_soup.select('select#selectQuality')[0]

		sources = []

		for option in quality_select.select('option'):
			quality = int(self.QUALITY_REGEX.search(option.text).group(1))
			src = base64.b64decode(option.get('value')).decode('utf-8')
			sources.append((quality, src))

		print('[KissAnime] Done Processing episode {}'.format(episode_number))

		return (episode_number, sources)