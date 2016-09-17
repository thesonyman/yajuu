import pytest

from yajuu.sources import Source, InvalidSourceException


def test_raise():
	source = Source('http://fake.com', quality=720, language='en')
	assert source

	with pytest.raises(InvalidSourceException):
		source = Source('http://fake.com')


def test_quality():
	source = Source('http://fake.com', quality=720, language='en')
	assert source.quality == 720

	source = Source('http://fake.com', quality=1080, language='en')
	assert source.quality == 1080


def test_language():
	source = Source('http://fake.com', quality=720, language='en')
	assert source.language == 'en'

	source = Source('http://fake.com', quality=720, language='und')
	assert source.language == 'und'
