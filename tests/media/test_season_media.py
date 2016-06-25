from unittest import TestCase

from yajuu.media.season_media import SeasonMedia


class DummySeasonMedia(SeasonMedia):
    class Episode(SeasonMedia.Episode):
        def _get_metadata(self):
            self.metadata['name'] = 'Dummy Episode'

    def __init__(self):
        super().__init__('Code Geass')

    def _update_metadata(self, query):
        pass

    def get_file_path(self):
        pass

    def list_files(self):
        pass

    def download(self):
        pass

    def __eq__(self, other):
                pass

    def __ne__(self, other):
        pass


class MediaSeasonTestcase(TestCase):
    def test_abstract(self):
        self.assertRaises(TypeError, SeasonMedia, '')

    def test_add_season(self):
        media = DummySeasonMedia()
        media._add_season(1)

        self.assertTrue(1 in media._seasons)
        self.assertRaises(ValueError, media._add_season, 1)

    def test_get_season(self):
        media = DummySeasonMedia()
        media._add_season(1)

        self.assertEqual(media.get_season(1), {})

    def test_add_episode(self):
        media = DummySeasonMedia()
        media._add_season(1)

        with self.assertRaises(KeyError):
            media._add_episode(0, None, None)

        with self.assertRaises(ValueError):
            media._add_episode(1, 'op-1', None)

        media._add_episode(1, 'op-1', DummySeasonMedia.Episode(1, 1))
        self.assertTrue(
            'op-1' in media._seasons[1],
            'The episode op-1 was not added to the list media._seasons[1].'
        )

    def test_get_episode(self):
        media = DummySeasonMedia()
        media._add_season(1)

        _episode = DummySeasonMedia.Episode(1, 1)
        media._add_episode(1, 'op-1', _episode)
        self.assertEqual(media.get_episode(1, 'op-1'), _episode)
