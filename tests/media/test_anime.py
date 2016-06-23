from unittest import TestCase
import mock
from contextlib import redirect_stdout

from yajuu.media import Anime


class AnimeTestcase(TestCase):
    def test_not_found(self):
        self.assertRaises(Anime.MediaNotFoundException, Anime, '')

    def test_title(self):
        code_geass = Anime('code geass')

        self.assertEqual(
            code_geass.metadata['name'],
            'Code Geass: Lelouch of the Rebellion'
        )

    def test_select(self):
        with redirect_stdout(None), \
             mock.patch('builtins.input', return_value='0'):
            Anime('code')
