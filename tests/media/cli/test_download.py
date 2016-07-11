import unittest
from unittest.mock import patch

from yajuu.cli.download import confirm_download
from yajuu.media import Movie


class DownloadTestCase(unittest.TestCase):

    def test_confirm_download(self):
        medias = [
            ('single')
        ]
