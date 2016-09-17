"""Sort different sources, and show some data about every one of them."""

import sys
sys.path.append('..')

import urllib.parse

from yajuu.sources import Source, SourceList, InvalidSourceException



def main():
	sources = SourceList()

	print('Please enter the urls of the source you want to analyse (ctrl+d when finished):')

	while True:
		try:
			url = input('> ')
		except EOFError:
			break

		try:
			source = Source(url)
		except InvalidSourceException:
			print('The source is invalid. Please try again with another one.')
			continue

		sources.add(source)

	print()

	for number, source in list(enumerate(sources.sort_by_speed())):
		print('#{} from {} ({}p)'.format(
			number + 1,
			urllib.parse.urlparse(source.url).netloc,
			source.quality
		))


if __name__ == '__main__':
	main()
