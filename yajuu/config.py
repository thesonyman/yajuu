"""Provides the config dict object. Will create it if not found."""

import os
import yaml

import click


DEFAULT_CONFIG = {
    'thetvdb': {
        'api_key': '34FF6CE86D796A6D',
        'language': 'en'
    },
    'media': {
        'preferred_quality': 1080,
        'minimum_quality': 720,
        'maximum_quality': 0
    },
    'paths': {
        'base': os.path.expanduser('~/Videos'),
        'medias': {
            'anime': {
                'base': 'Anime',
                'season': 'Season {season_number:02d}',
                'episode': '{anime_name} - S{season_number:02d}e{episode_number:03d}.{ext}'
            },
            'movie': {
                'base': 'Movies',
                'file': '{movie_name} ({movie_date}).{ext}'
            }
        }
    },
    'plex_reload': {
        'enabled': False,
        'token': '',
        'base_url': '',
        'sections': {
            'Anime': [],
            'Movie': []
        }
    },
    'misc': {
        'downloader': 'wget {filename} {url}'
    }
}

config_path = os.path.join(click.get_app_dir('yajuu'), 'config.yaml')
config = None


def check_config(expected, given):
    """Recursive function to check the configuration passed by the user."""

    config = {}

    for key, value in expected.items():
        if key in given:
            if type(value) == dict:
                if isinstance(given[key], dict):
                    config[key] = check_config(value, given[key])
                else:
                    config[key] = value
            else:
                if isinstance(given[key], type(value)):
                    config[key] = given[key]
                else:
                    config[key] = value
        else:
            config[key] = value

    return config


def save_config():
    global config

    with open(config_path, 'w+') as file:
        file.write(yaml.dump(config, default_flow_style=False))


if os.path.exists(config_path):
    with open(config_path, 'r') as file:
        config = check_config(DEFAULT_CONFIG, yaml.load(file))
else:
    config = DEFAULT_CONFIG
    os.makedirs(os.path.dirname(config_path))
    save_config()
