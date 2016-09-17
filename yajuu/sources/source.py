from enum import Enum

from yajuu.sources import FFProbe


class Source:

    """Represent a source, an url to an online file.
    
    Attributes:
        LANGUAGES: a list of all the supported languages
        VERSIONS: a list of all the supported versions

    """

    LANGUAGES = Enum('languages', 'en fr ja und')

    VERSIONS = Enum('versions', 'sub dub raw')

    def __init__(self, url, quality=None, language=None, version=None):
        '''Instantiate the source descriptor.

        Raises:
            sources.exceptions.InvalidSourceException
        '''

        self.url = url
        self.version = version if version else self.VERSIONS.sub

        if quality is None or language is None:
            self._ffprobe = FFProbe(self.url)

        if quality is None:
            self.quality = self._ffprobe.video_stream['height']
        else:
            self.quality = quality

        if language is None:
            tag = self._ffprobe.video_stream['tags']['language']

            if hasattr(self.LANGUAGES, tag):
                self.language = getattr(self.LANGUAGES, tag)
            else:
                self.language = self.LANGUAGES.und
        else:
            self.language = language

        self.response_time = None
