"""Provides the base implementation of the media class."""

import logging
from abc import ABCMeta, abstractmethod

from yajuu.cli.asker import Asker
from yajuu.cli.media.download.downloader import download_file


class Media(metaclass=ABCMeta):

    """Abstract class for a media.

    It should represent for example a movie, or a tv show. This class can be
    used to get all sort of information from the media type, or the element
    itself.

    It also contains the logic to download the specific type of media.

    """

    class MediaNotFoundException(Exception):

        """Thrown when a media could not be found."""

        pass

    def __init__(self, query):
        """Initialize the media.

        Args:
            query (str): The string to search for (media name).

        """

        self.logger = logging.getLogger(__name__)
        self.asker = Asker.factory()
        self.query = query

        # Contains all the metadata about the media (name, date, ..)
        self.metadata = {}

        # Fetch the metadata
        self._update_metadata()

    @abstractmethod
    def _update_metadata(self):
        """Update the self.metadata object by fetching data.

        Also searches to get the correct result. May use the _select_result
        method to select the correct result.

        Note:
            You MUST implement the 'id' key, or edit the __eq__ method. The
            metadata should also include the 'name' key.

            You should not add media prefixes, such as 'movie_id'.

        Returns:
            None: Nothing, as the metadata is stored in the self.metadata dict.

        """

        pass

    @abstractmethod
    def get_path_config(self):
        """Get the path configuration relative to the media.

        The dict should be stored in config['path']['medias'][MEDIA_TYPE].

        Note:
            See the config.py file, in the root folder.

        Returns:
            dict: The configuration.

        """

        pass

    def download(self, sources, dump=False):
        """Contains the logic to download each needed file.

        It should call the cli/downloader.py download_file method.

        Args:
            sources (dict): Sources extracted using an orchestrator.
            dump (bool): Whether you need to dump the source or download it.

        Returns:
            None: nothing should be returned, any result will be ignored.

        """

        # Logic to download a single file (movie, ..)

        path_params = {
            'name': self.metadata['name'],
            'date': self.metadata['year'] if 'year' in self.metadata else 'N/A'
        }

        file_format = self.get_path_config()['file']

        download_file(dump, self, file_format, path_params, sources)

    def _select_result(self, results):
        """Basic method to select the correct result from a list.

        When the media class is constructed, somtimes we need to prompt the
        user for the correct title. This method provides a basic
        implementation.

        Note:
            This method trims the results to a maximum of 10 items. Duplicates
            will be removed.

        Args:
            results (list): A list of items to select.

        Returns:
            The returned value of the selected item, or None if the user
            cancelled.

        """

        # Remove the duplicates (title only)
        filtered_results = []
        filtered_keys = []

        for result in results:
            if result[1] not in filtered_keys:
                filtered_results.append(result)
                filtered_keys.append(result[1])

        # Filter to ten results
        results = results[:10]

        return self.asker.select_one(
            "Which title is correct for input '{}'?".format(self.query),
            [(x[1], x[0]) for x in results]
        )

    def __eq__(self, other):
        """Defines whether a media object is the same as another one.

        This method check for the id on the metadata object by default.

        Returns:
            bool: whether it is the same.

        """

        self_id = self.metadata['id']
        other_id = other.metadata['id']

        return isinstance(other, self.__class__) and self_id == other_id

    def __ne__(self, other):
        """Defines whether a media object is NOT the same as another one.

        This method returns the opposite of the __eq__ method by default.

        Returns:
            bool: whether it NOT is the same.

        """

        return not self.__eq__(other)
