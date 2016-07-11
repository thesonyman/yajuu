import unittest
from unittest.mock import patch, mock_open

from yajuu.config import check_config, DEFAULT_CONFIG, save_config, config_path


class ConfigTestCase(unittest.TestCase):

    def test_check_config(self):
        # The config should not be edited if every parameter is correct
        self.assertEquals(
            DEFAULT_CONFIG, check_config(DEFAULT_CONFIG, DEFAULT_CONFIG)
        )

        # It should eliminate the invalid fields
        self.assertEquals(
            {
                'a': '',
                'b': {'c': ''}
            },
            check_config(
                {'a': '', 'b': {'c': ''}},
                {'d': '', 'b': {'e': ''}}
            )
        )

        # It should edit the fields that have the sample value
        self.assertEquals(
            {'hello': 'world'},
            check_config({'hello': ''}, {'hello': 'world'})
        )

        # It should also edit the ones in sub-dicts
        self.assertEquals(
            {'hello': {'world': 'lorem'}},
            check_config(
                {'hello': {'world': ''}},
                {'hello': {'world': 'lorem'}}
            )
        )

    def test_save_config(self):
        # Well, we just assert that the file is correctly openned

        with patch('builtins.open', mock_open()) as mock:
            save_config()
            mock.assert_called_with(config_path, 'w+')
