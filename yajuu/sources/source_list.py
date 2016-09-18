import time
import urllib

import requests
from requests.exceptions import ConnectTimeout, ReadTimeout

from yajuu.sources.source import Source


class SourceList:

	"""Simple way to organize sources (yajuu.media.Source) and sort / filter them.

	This class WILL make connections and download a bit of the file to sort
	them by	speed.

	Note:
		You can use list on this class to get it as a list, instead of getting
		the _sources list (eg: use list(sources) instead of sources._sources).

	"""

	def __init__(self, sources=[]):
		'''Initialize the class.

		Args:
			sources (list): an already filled list of sources.

		'''
		self._sources = sources

	def add(self, source):
		'''Adds a class to the inner list.

		Args:
			source (yajuu.sources.Source)

		'''

		self._sources.append(source)

	def __iter__(self):
		'''Iterates over the internal source list.'''

		return iter(self._sources)

	def __add__(self, other):
		return SourceList(sources=self._sources + other._sources)

	def filter(self, min_quality=None, max_quality=None, language=None, version=None):
		'''Yield the sources that follow the wanted rules.

		Args:
			min_quality (int)
			max_quality (int)
			language (str)
			version (str)

		Note:
			See the yajuu.sources.Source class for more information about the
			language and versions arguments.

		'''

		for source in self._sources:
			if min_quality is not None and source.quality < min_quality:
				continue

			if max_quality is not None and source.quality > max_quality:
				continue

			if language is not None and source.language != language:
				continue

			if version is not None and source.version != version:
				continue

			yield source

	def sort_by_speed(self, output=True):
		'''Sorts the sources by speed, still preferring quality over speed.

		Args:
			ouptut (bool): whether to show the messages or not.

		Note:
			You can access the raw response time: it's stored in all the
			sources as 'response_time'.

		Returns:
			Yield the sources, grouped by quality but all separately.

			Example:
			for source in sources.sort_by_speed():
				print(source.response_time, source.quality, source.url)

		'''

		sources = self._sources

		if output:
			# So we can align the messages
			max_length = max([len(urllib.parse.urlparse(x.url).netloc) for x in sources])

		# First, group the sources by quality, since we prefer quality over speed.
		by_quality = {}

		for source in sources:
			if source.quality not in by_quality:
				by_quality[source.quality] = []

			by_quality[source.quality].append(source)


		# Then, calculate the speed of each source and yield them accordingly
		for quality in sorted(by_quality, reverse=True):
			if len(by_quality[quality]) <= 1 and output:
				print('Only one source available for quality {}.'.format(
					quality
				))

				yield by_quality[quality][0]
				continue

			if output:
				print('Testing {} sources'.format(len(by_quality[quality])))

			for source in by_quality[quality]:
				netloc = urllib.parse.urlparse(source.url).netloc
				offset = max_length - len(netloc)

				base = 'Testing source at {}.. {}'.format(netloc, ' ' * offset)

				if output:
					print(base, end='\r', flush=True)

				try:
					response = requests.get(
						source.url, stream=True, timeout=5,
						headers={'Connection': 'close'}
					)
				except (ConnectTimeout, ReadTimeout):
					print('{} timed out'.format(base))
					continue

				test_size = 1e6  # In bytes

				start = time.time()
				downloaded = 0

				for chunk in response.iter_content(chunk_size=1024):
					downloaded += len(chunk)

					print('{} {} bytes'.format(base, downloaded), end='\r', flush=True)

					if downloaded >= test_size:
						break

				response.close()

				source.response_time = time.time() - start

				print('{0} {1} bytes downloaded in {2:.2f} seconds'.format(
					base, downloaded, source.response_time
				))

			yield from sorted(by_quality[quality], key=lambda x: x.response_time)