import re
import json
import concurrent.futures

import execjs

from . import AnimeExtractor
from .. import unshorten

class MasteraniExtractor(AnimeExtractor):
	MIRRORS_REGEX = re.compile(r'var args = ({[.\s\S]+?)</script>')

	def _get_url(self):
		return 'http://www.masterani.me'

	def search(self):
		data = self.session.get(
			'http://www.masterani.me/api/anime-search', params={
				'keyword': self.media.metadata['name']
			}
		).json()

		results = []

		for item in data:
			results.append((item['title'], (item['id'], item['slug'])))
		
		return results

	def extract(self, season, result):
		id, slug = result[1]

		episodes = self.session.get(
			'http://www.masterani.me/api/anime/{}/detailed'.format(id)
		).json()[0]['episodes']

		sources = {}

		with concurrent.futures.ThreadPoolExecutor(16) as executor:
			for episode_number, _sources in executor.map(self.episode_worker, [
				(slug, episode) for episode in episodes
			]):
				if episode_number not in sources:
					sources[episode_number] = []

				sources[episode_number] += _sources

		return sources

	def episode_worker(self, data):
		slug, episode_details = data

		number = int(episode_details['episode'])

		print('[Masterani] Processing episode {}'.format(number))

		url = 'http://www.masterani.me/anime/watch/{}/{}'.format(slug, number)

		# We extract the object hard-coded, and translate it to json.
		mirrors = json.loads(execjs.eval('JSON.stringify({})'.format(
			self.MIRRORS_REGEX.search(self.session.get(url).text).group(1)
		)))['mirrors']

		sources = []

		for mirror in mirrors:
			suffix = mirror['host']['embed_suffix']

			if not suffix:
				suffix = ''

			url = (
				mirror['host']['embed_prefix'] + mirror['embed_id'] +
				suffix
			)

			mirror_sources = unshorten(url, quality=mirror['quality'])

			if mirror_sources:
				sources += mirror_sources
			else:
				with open('test.txt', 'w') as file:
					file.write(url)

				print(url)

		return (number, sources)
