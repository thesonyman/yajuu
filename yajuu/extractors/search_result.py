import re

from yajuu.media import Source


class SearchResult:

    def __init__(self, media, title, identifier, version=None, lang=None):
        if version is None:
            version = Source.VERSIONS.sub

        self.version = version

        if lang is None:
            lang = Source.LANGUAGES.en

        self.lang = lang

        self.title = self._parse_title(title)
        self.identifier = identifier

    @classmethod
    def from_tuples(cls, media, data):
        return [cls(media, *x) for x in data]

    @classmethod
    def from_links(cls, media, data):
        return cls.from_tuples(media, [
            (
                re.sub(r'[\r\n]', '', x.text.strip()),
                x.get('href')
            ) for x in data
        ])

    def _parse_title(self, title):
        version_regex = re.compile(r'\s?\(([SsdD]ub)\)\s?')
        results = version_regex.search(title)

        if not results:
            return title

        version = results.group(1).lower()
        self.version = getattr(Source.VERSIONS, version)

        return re.sub(version_regex, '', title)

    def __repr__(self):
        return '<SearchResult version="{}" title="{}">'.format(
            self.version.name, self.title
        )
