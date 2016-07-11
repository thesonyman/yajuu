import unittest
from unittest.mock import Mock, patch

import plexapi
from click.testing import CliRunner

from yajuu.cli.configure import (
    get_plex_account, get_plex, get_selected_sections, plex
)
from yajuu.config import config


class ConfigureTestCase(unittest.TestCase):
    @patch('yajuu.cli.configure.inquirer.prompt')
    @patch('yajuu.cli.configure.plexapi.myplex.MyPlexAccount.signin')
    def test_get_account(self, mock_signin, mock_prompt):
        mock_prompt.return_value = {
            'username': '',
            'password': ''
        }

        # With no credidentials, the cli should call sys.exit
        self.assertRaises(SystemExit, get_plex_account)

        mock_prompt.return_value = {
            'username': 'hello',
            'password': 'world'
        }

        mock_signin.side_effect = plexapi.exceptions.Unauthorized

        # With fake credidentials, the cli should also call sys.exit
        self.assertRaises(SystemExit, get_plex_account)

        mock_prompt.return_value = {
            'username': 'hello',
            'password': 'world'
        }

        mock_signin.side_effect = None

        # Finally, with right credidentials we should get the mock object back
        self.assertTrue(get_plex_account() is not None)

    @patch('yajuu.cli.configure.inquirer.prompt')
    def test_get_plex(self, mock_prompt):
        account = Mock()

        resource = Mock()
        resource.name = 'localhost'
        resource.connect.return_value = 'connected'

        account.resources.return_value = [resource]

        # The method should call sys.exit if the user cancelled
        mock_prompt.return_value = None
        self.assertRaises(SystemExit, get_plex, account)

        # The method should return the correct selected server
        mock_prompt.return_value = {'server': 'localhost'}
        self.assertEquals(get_plex(account), 'connected')

    @patch('yajuu.cli.configure.inquirer.prompt')
    def test_get_selected_sections(self, mock_prompt):
        _plex = Mock()
        _plex.library.sections.return_value = {}

        # The method should exit if no data was passed.
        mock_prompt.return_value = None
        self.assertRaises(SystemExit, get_selected_sections, _plex)

        section = Mock()
        section.title.return_value = 'movie'
        _plex.library.sections.return_value = [section]

        sample_section = 'hello-world'
        mock_prompt.return_value = {'sections': sample_section}

        # Else, it should bind each section to the passed value
        self.assertEquals(get_selected_sections(_plex), {
            x: sample_section for x in config['plex_reload']['sections']
        })
