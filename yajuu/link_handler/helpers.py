"""Set of helpers dedicated to the link handlers."""

import re


def extract_pattern(pattern):
	'''Decorator to easilly extract a pattern (like an id) from the url. Will
	abort the operation if the pattern fails to match.

	Note:
		You can use multiple capturing groups, just add an argument in the
		method declaration, eg:

			def handle_link(identifier, quality, *args, **kwargs):
				pass

	Usage:
		@extract_pattern(r'.+')
		def handle_link(identifier, *args, **kwargs):
			pass

	'''

	def decorator(method):
		def wrapper(url, *args, **kwargs):
			results = re.findall(pattern, url)

			if len(results) == 0:
				return None

			return method(*results, *args, **kwargs)
		return wrapper
	return decorator
