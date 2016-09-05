import pytest


from yajuu.media import Media, bootstrap_provider


def test_media_construct():
	berserk = Media(bootstrap_provider('anime'), 'Berserk (2016)')

	assert berserk.title == 'Berserk (2016)'
	assert berserk.type == 'anime'
	assert all(getattr(berserk, x) for x in ['id', 'title', 'seasons'])


def test_media_equals():
	berserk = Media(bootstrap_provider('anime'), 'Berserk (2016)')
	jormungand = Media(bootstrap_provider('anime'), 'Jormungand')


	assert getattr(jormungand, 'id') is not None
	assert getattr(jormungand, 'title') is not None
	assert getattr(jormungand, 'seasons') is not None

	assert jormungand != berserk


def test_media_select():
	class FakerAsker:

		def __init__(self):
			self.called = False

		def select_result(self, message, data):
			self.called = True

			return [x for x in data if x[0] == 'Hellsing'][0][1]

	asker = FakerAsker()

	# The search results also return 'Helmsing Ultimate' and 'Hellsing Ultimate Abridged'
	hellsing = Media(bootstrap_provider('anime'), 'Hellsing', select=asker.select_result)

	assert hellsing.title == 'Hellsing'
	assert asker.called


def test_media_inexistent():
	with pytest.raises(Media.NotFoundException):
		Media(bootstrap_provider('anime'), 'this does not exist')
