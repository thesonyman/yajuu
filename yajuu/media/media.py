from yajuu.media.providers import bootstrap_provider


class Media:

	"""Fetch metadata about a media, and represent it in a simple way.

	After searching for the provided query using a 'provider', this class
	store the result in a dict called '_metadata'. You can access this dict
	directly, through the __getattr__ method (eg: media.title).

	Note:
		You can use the class method 'create' to avoid importing providers
		manually.

	"""

	def __init__(self, provider, query, select_result=None):
		"""Instantiate the media class by fetching the required metadata.

		Args:
			provider (func): the method used to fetch all the metadata.

		"""

		self._metadata = provider(query)

		if self._metadata is None:
			raise Exception('The media could not be found.')

	def __getattr__(self, key):
		return self._metadata[key]
