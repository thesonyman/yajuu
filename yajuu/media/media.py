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

		result = provider(query)

		if result is None:
			raise Exception('The media could not be found.')

		self.type, self._metadata = result

	def __getattr__(self, key):
		'''Tries to get the correspoding key in the self._metadata dict.'''

		return self._metadata[key]

	def __eq__(self, other):
		'''Defines using the metadata id whether or not the other media is the same.'''

		return (
			isinstance(other, self.__class__) and
			self.type == other.type and
			self.id == other.id
		)

	def __ne__(self, other):
		'''Uses the __eq__ method to define whether the other media object is different.'''

		return not self.__eq__(other)
