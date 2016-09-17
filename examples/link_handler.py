"""Skip the player / media host bakavideo, and show the 'real' download link."""

import sys
sys.path.append('..')

from yajuu.link_handler import handle_link


def main():
	link = 'https://bakavideo.tv/embed/09E9Ba7DI'
	print('Getting sources from video at {}..'.format(link))

	sources = handle_link(link)

	for index, source in enumerate(sources):
		print('#{} - {} ({}p)'.format(index + 1, source.url, source.quality))


if __name__ == '__main__':
	main()
