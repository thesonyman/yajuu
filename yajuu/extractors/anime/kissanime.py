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
	TOKENS_REGEX = re.compile(
		'var s,t,o,p,b,r,e,a,k,i,n,g,f, ([a-zA-Z]+)={"([a-zA-Z]+)":(.+)};'
		'[.\s\S]+?;(.+);a.value'
	)

	EPISODE_REGEX = re.compile('.+ Episode (\d{3,})')

	QUALITY_REGEX = re.compile('(\d{3,})p')

	def __init__(self, media, season):
		super().__init__(media, season)

		self.session = cfscrape.create_scraper()
		self.session.headers['User-Agent'] = (
			'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like '
			'Gecko) Chrome/41.0.2228.0 Safari/537.36'
		)

	def _check_browser(self):
		'''The kissanime website does have an internal security, which asks you
		to wait 5 seconds. We need to pass that.'''

		response = self.session.get('https://kissanime.to')

		if 'Please wait 5 seconds...' not in response.text:
			return

		soup = bs4.BeautifulSoup(response.text, 'html.parser')

		# Okay, so the page uses javascript to compute a validation code. We
		# can use a regex to extract the essential parts of the code, and then
		# execute the parts hard to parse.

		# First, get the variables necessary to run the javascript code
		javascript_parts = self.TOKENS_REGEX.search(response.text)

		object_name = javascript_parts.group(1)
		object_key = javascript_parts.group(2)  # The sub-object (dict)
		object_value = javascript_parts.group(3)
		object_modifier = javascript_parts.group(4)  # The code hard to parse
		domain_len = len('kissanime.to')

		# Now we can generate a little bit of javascript to wrap the modifier
		code = '''
		(function() {
			var {object_name} = {{ {object_key}: {object_value} }};
			{object_modifier};
			return parseInt({object_name}.{object_key} + {domain_len}, 10);
		})()
		'''.format(
			object_name=object_name, object_key=object_key,
			object_value=object_value, object_modifier=object_modifier,
			domain_len=domain_len
		)

		# And execute it
		jschl_answer = execjs.eval(code)

		# Now we need to extract the other tokens, including the post url
		submit_url = submit_url = soup.select(
			'#challenge-form'
		)[0].get('action')

		payload = {
			'jschl_answer': jschl_answer,
			'jschl_vc': soup.select('input[name=jschl_vc]')[0].get('value'),
			'pass': soup.select('input[name=pass]')[0].get('value')
		}

		# Before submitting the request, we need to sleep
		time.sleep(4)

		# And tada!
		session.get('https://kissanime.to' + submit_url, params=payload)

	def search(self):
		self._check_browser()

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
			for episode_number, extractor_sources in executor.map(
				self.episode_worker,
				soup.select('table a[href^="/Anime/"]')
			):
				if episode_number not in sources:
					sources[episode_number] = []

				sources[episode_number] += extractor_sources

		return sources

	def episode_worker(self, link):
		url = 'https://kissanime.to' + link.get('href')
		episode_number = int(self.EPISODE_REGEX.search(link.text).group(1))
		print('[KissAnime] Processing episode {}'.format(episode_number))

		episode_soup = self._as_soup(url, method='get')

		quality_select = episode_soup.select('select#selectQuality')[0]

		sources = []

		for option in quality_select.select('option'):
			quality = int(self.QUALITY_REGEX.search(option.text).group(1))
			src = base64.b64decode(option.get('value')).decode('utf-8')
			sources.append((quality, src))

		print('[KissAnime] Done Processing episode {}'.format(episode_number))

		return (episode_number, sources)
