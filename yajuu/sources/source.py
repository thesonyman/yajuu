from yajuu.sources import FFProbe


class Source:

    """Represent a source, that's to say an url to an online file and it's
    metadata. Gets needed metadata by itself if needed.

    If not specified, this class will try to get metadata about the stream,
    that's to say it's quality or language. If you already know the quality and
    language  (the two values that can be extracted automatically), pass them.
    It will reduce the run time, as we won't have to call an external tool.

    You can pass whatever value for the language and versions, but you should
    stick to the conventions: the country code for the language ('und' if
    unknown) and either 'sub', 'dub', 'raw' or 'und' for the versions.

    """

    def __init__(self, url, quality=None, language=None, version=None):
        '''Instantiate the source descriptor.

        Args:
            quality (int): the height of the stream.
            language (str): the country code of the language.
            version (str): the 'version' of the video stream (sub, dub, ..)

        Raises:
            sources.exceptions.InvalidSourceException

        '''

        self.url = url
        self.version = version if version else 'sub'

        if quality is None or language is None:
            self._ffprobe = FFProbe(self.url)

        if quality is None:
            self.quality = self._ffprobe.video_stream['height']
        else:
            self.quality = quality

        if language is None:
            tag = self._ffprobe.video_stream['tags']['language']
            self.language = tag
        else:
            self.language = language

        self.response_time = None
