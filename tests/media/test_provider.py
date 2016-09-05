import types
import pytest


from yajuu.media import bootstrap_provider


def test_bootstrap_provider_return_function():
	provider = bootstrap_provider('anime')
	assert isinstance(provider, types.FunctionType)


def test_bootstrap_provider_return_none():
	assert bootstrap_provider('nonexistent') is None


def test_valid_provider():
	provider = bootstrap_provider('anime')
	_type, metadata = provider('Berserk (2016)')

	assert _type == 'anime'
	assert all(x in metadata for x in ['id', 'title', 'seasons'])
