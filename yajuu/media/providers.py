'''Defines the providers: single methods that fetch metadata about a media.


Note:
	This imports should be lazy: we don't want to import all the dependencies
	for each media type when we just want to fetch one media type.

'''


def bootstrap_provider(type):
	'''Loads the correct provider for the type, and return the method.

	Args:
		type (str): the type of provider to use. See the initial if statement.

	'''

	if type == 'anime':
		return anime_provider
	else:
		return None


def anime_provider(query):
	'''Provides anime metadata using the tvdb api.

	Args:
		query (str): the query to search for

	Returns:
		tuple: the media type, and the metadata.
		None: if the media could not 

	'''

	from yajuu.asker import Asker
	from pytvdbapi import api
	from pytvdbapi.error import TVDBIndexError


	database = api.TVDB('34FF6CE86D796A6D')
	asker = Asker.factory()
	select_result = asker.select_one

	try:
		results = database.search(query, 'en')

		if len(results) == 0:
			return None
		elif len(results) == 1:
			show = results[0]
		else:
			identifier = select_result('Please select the correct title', list(
				(x.SeriesName, x.id) for x in results
			))

			# We'll use the last iteration show variable
			for show in results:
				if show.id == identifier:
					break

		# Fetch the metadata
		show.update()
	except TVDBIndexError:
		raise not_found_exception

	metadata = {}
	metadata['id'] = show.id
	metadata['title'] = show.SeriesName
	metadata['seasons'] = {}

	for season in show:
		season_data = {}

		for episode in season:
			episode_data = {'name': episode.EpisodeName}

			season_data[episode.EpisodeNumber] = episode_data

		metadata['seasons'][season.season_number] = season_data

	return 'anime', metadata
