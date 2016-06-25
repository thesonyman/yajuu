from unittest import TestCase

from yajuu.media.media import Media


class MediaTestcase(TestCase):
    def test_abstract(self):
        self.assertRaises(TypeError, Media, '')

    def test_keep_query(self):
        class SimpleMedia(Media):
            def _update_metadata(self, query):
                pass

            def list_files(self):
                pass

            def download(self):
                pass

            def __eq__(self, other):
                pass

            def __ne__(self, other):
                pass

        query = 'hello world'
        media = SimpleMedia(query)
        self.assertEqual(media.metadata, {'query': query})
