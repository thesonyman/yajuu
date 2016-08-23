"""Searchs for an anime, and prints out the root information."""

import sys
sys.path.append('..')

from yajuu.media import Media, bootstrap_provider



def main():
	if len(sys.argv) != 2:
		print('Please provide the query as the first argument.')
		sys.exit(1)

	media = Media(bootstrap_provider('anime'), sys.argv[1])

	print('Id: {}'.format(media.id))
	print('Title: {}'.format(media.title))

	print('\n---\n')

	for number, episodes in media.seasons.items():
		print('=> Season {}'.format(number))

		for episode_number, episode in episodes.items():
			print('-> Episode {}: {}'.format(episode_number, episode['name']))

		print()


if __name__ == '__main__':
	main()
