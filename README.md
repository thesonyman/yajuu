# Yajuu: an automated media downloader

[![Build Status](https://travis-ci.org/vivescere/yajuu.svg?branch=develop)](https://travis-ci.org/vivescere/yajuu)
[![Coverage Status](https://coveralls.io/repos/github/vivescere/yajuu/badge.svg?branch=develop)](https://coveralls.io/github/vivescere/yajuu?branch=develop)

**This software is in beta. It only supports the download of anime for now. Music, movies and TV shows are to be added. No GUI is available for now, so you will have to use the CLI.**

Yajuu, which stands for wild beast in Japanese, is a software that can help you in the fastidious task of downloading files from the internet. It search on known websites for what you want, asks you which result is correct and then proceed to download the medias. By default, it uses ```wget``` to download files, and follow [the plex recommendations](https://support.plex.tv/hc/en-us/categories/200028098-Media-Preparation) as of file naming conventions.

It's made to be simple to use, just see it in action:
<p align="center">
	<a href="https://asciinema.org/a/ckiegvcdlwo0i5esm8e2kghzs" target="_blank">
		<img src="https://asciinema.org/a/ckiegvcdlwo0i5esm8e2kghzs.png" alt="Asciinema recording">
	</a>
</p>

## Table of contents
 - [Installation](#installation)
 - [Supported medias and websites](#supported-medias-and-websites)
 - [Usage](#usage)
 - [Configuration](#configuration)
 - [Development](#development)
 - [License](#license)

## Installation
```bash
git clone https://github.com/vivescere/yajuu.git
cd yajuu
sudo python setup.py install
```

# Supported medias and websites
Here is the complete list:
 - Animes:
  - [http://www.animechiby.com](http://www.animechiby.com)
  - [http://animehaven.org](http://animehaven.org)
  - [http://gogoanime.io](http://gogoanime.io)
  - [http://htvanime.com](http://htvanime.com)
  - [http://www.masterani.me](http://www.masterani.me)
  - [http://rawranime.tv](http://rawranime.tv)

The list of the sites that are to be added next is available on the project [trello board](https://trello.com/c/EhsCIloT/3-sites-to-support).

## Usage
The only available mode is the download one, for now. A 'repair' mode is planned, which should be able to rename your files, check for invalid ones or with a too low quality, ...

*Note:* The files that you download can be watermarked. The program will try to avoid that, but it can still happen.

You can also use the *--help* flag on the root or sub commands.

### Root options
The --verbosity option sets the logger versbosity and accept the following values: CRITICAL, ERROR, WARNING, INFO and ERROR.

The --media-type option sets the media type for ALL the passed medias, and accept the following values: anime.

### Download
Simple use the --media option of the download section:

```bash
yajuu media download --media 'Code geass season 1'
```

You can pass it multiple times:
```bash
yajuu media download --media 'Code geass season 1' --media 'Berserk season 1'
```

And request more than one season:
```bash
yajuu media download --media 'Psycho-Pass seasons 1,2'
```

## Configuration
The config file is normally located at :
 - *~/.config/yajuu/config.yaml* on linux
 - *~/Library/Application Support/yajuu/config.yaml* on Mac OS X
 - *C:\Users\<user>\AppData\Roaming\yajuu\config.yaml* on Windows

### Media quality
In the *media* section, you can edit:
 - *minimum_quality*, by default set to 720.
 - *maximum_quality*, by default set to 0, which means no limitations.

### Download paths
The base path is set by default to *~/Videos*. The other parameters are all relatives to that base, and uses the plex naming recommendations by default.

### Plex reloader
By setting the enabled variable to true, you will enable the plex reloader, which triggers a library reload after each episode is downloaded.

You will need to configure the sections array, which is case sensitive.

### Custom downloader
Yajuu uses wget by default, but you can use virtually anything. Here are the variables (automatically quoted) that you can use while building the command :
 - *dirname*: the absolute path to the download folder
 - *filename*: the name of the file
 - *filepath*: the full path, including the dir and name to the file
 - *url*: the url to the online file

Here is an example for [aria2](https://aria2.github.io/) :
```yaml
misc:
  downloader: 'aria2c -x 5 -s 5 --summary-interval 0 --console-log-level error --download-result hide -d {dirname} -o {filename} {url}'
```


### Thetvdb
This project relies on [thetvdb](http://thetvdb.com/) to find the correct medias names. A default key is included, but you can change it the default one does not work. You can also change the search language.

## Development

You are welcome to contribute to the project, any help will be appreciated! However, you must be using [git flow](https://github.com/nvie/gitflow) to help.

### To create an extractor (add a website)
Create a file in the extractors package, called '<website>_extractor'. You should create it in the sub-package specific to the media type that the site supports.

Please inspire you from the existing files, to use for example threading. Each extractor should extends from a parent class. The mother class is called *Extractor*, but there are sub-classes that can be extended too, such as the *SeasonExtractor* class.

Usually, you will just have to create two methods: *search* and *extract*.

The search method should return an array of tuples. Each tuple should contain two variables, the first one being the string displayed to the user, the second an identifier that can be what you want (an url, a slug, ...).

The extract method parameters and return values can vary. In all case, the passed result variable is the one of the tuples returned by the search method. For example, using the season extractor you will also have access to the season variable. This method should be threaded, and use at most 16 threads. It should return a dict, at least for seasoned medias, which should have as key the episode number and as value a source array. Else, just return a source array. The source array is a simple list of tuples, each containing first the quality of the stream as an integer, and secondly the direct link to the source.

For example, you could write:
```python
from .anime_extractor import AnimeExtractor

class AnimeChibyExtractor(AnimeExtractor):
	def search(self):
		# Do some requests, etc...
		return [('First result', 'http://fake', ...)]

	def extract(self, season, result):
		# Do some other requests there.
		return {
			1: [
				(1080, 'http://fake'),
				..
			],
			..
		}
```


Then, you will need to add your extractor to the corresponding orchestrator. For example, you added an anime site, edit the anime/anime_orchestrator.py file. All you have to do is to import your extractor, and add it to the *_get_default_extractors* method.

### Using the unshorten helper
The unshorten file in the extractors module expose the *unshorten* method, which can be used to extract sources from well known sites, and also the *get_quality* method to get the quality of a stream. You can add websites to this file, this will be very appreciated.

To get the quality of a stream, you can use the get_quality method, which will return an integer.

The unshorten method checks if it knows the given website. If it doesn't, it returns None. Else, it extract the available sources, and return them as a [source array](### To create an extractor (add a website)).

## License
Yajuu uses the [GNU](LICENSE) general public license.
