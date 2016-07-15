from enum import Enum


class Source:
    LANGUAGES = Enum('languages', 'en')
    VERSIONS = Enum('versions', 'sub dub raw')

    def __init__(self, url, quality, lang=None, version=None):
        self.url = url
        self.lang = lang if lang else self.LANGUAGES.en
        self.version = version if version else self.VERSIONS.sub
        self.quality = quality

    def __repr__(self):
        return '<Source quality={} url="{}">'.format(
            self.quality, self.url
        )
