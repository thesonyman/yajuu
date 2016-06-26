from . import AnimeExtractor

class MasteraniExtractor(AnimeExtractor):
	def search(self):
		soup = self._get('http://www.masterani.me/anime', params={
			'search': self.media.metadata['name']
		})

		results = []

		print(soup.prettify())

		for link in soup.select('.info > a'):
			results.append((link.text, link.get('href')))

		return results

	def extract(self, season, result):
		return []
