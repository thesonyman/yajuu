import re

from yajuu.media.sources.source import Source


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
        version_regex = r'\s?\(([SsdD]ub)(?:bed)?\)\s?'
        results = re.search(version_regex, title)

        if not results:
            return title

        version = results.group(1).lower()
        self.version = getattr(Source.VERSIONS, version)

        return re.sub(version_regex, '', title)

    def __repr__(self):
        return '<SearchResult identifier="{}" title="{}">'.format(
            self.identifier, self.title
        )
