from yajuu.sources import Source, SourceList


def test_source_list_basic():
	sources = SourceList()
	source = Source('http://fake.com', quality=720, language='en')
	sources.add(source)

	assert list(sources) == [source]


def test_source_list_sorted():
	hd = [Source('http://fake.com', quality=720, language='en') for x in range(5)]
	sd = [Source('http://fake.com', quality=480, language='en') for x in range(5)]
	fr = [Source('http://fake.com', quality=720, language='fr') for x in range(5)]
	dub = [Source('http://fake.com', quality=720, language='en', version='dub') for x in range(5)]

	all_sources = hd + sd + fr + dub

	sources = SourceList(all_sources)

	assert list(sources.filter()) == all_sources
	assert list(sources.filter(min_quality=720)) == hd + fr + dub
	assert list(sources.filter(max_quality=480)) == sd
	assert list(sources.filter(language='fr')) == fr
	assert list(sources.filter(version='dub')) == dub
