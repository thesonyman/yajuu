import subprocess
import json

from yajuu.sources import InvalidSourceException


class FFProbe:

	"""Simple wrapper arround the ffprobe json api.

	This should work with ffprobe or avprobe. You can access the _raw object,
	but should propbably use the video_stream and other helpers (eg:
	self.streams). Go ahead and the commands yourself to see the available
	keys.

	"""

	def __init__(self, url):
		'''Executes ffprobe, and extracts the informations from the json output.

		Raises:
			yajuu.sources.InvalidSourceException

		'''

		command = [
			'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
			'-show_streams', url
		]

		process = subprocess.Popen(command, stdout=subprocess.PIPE)
		out = process.communicate()[0].decode('utf-8')

		if process.returncode != 0 or out == '':
			raise InvalidSourceException()

		self._raw = json.loads(out)

		if self._raw == {}:
			raise InvalidSourceException()

		self.streams = {}

		for stream in self._raw['streams']:
			if stream['codec_type'] not in self.streams:
				self.streams[stream['codec_type']] = []

			self.streams[stream['codec_type']].append(stream)

	@property
	def video_stream(self):
		'''Returns the first video stream, or None.'''

		if 'video' not in self.streams:
			return None

		return self.streams['video'][0]
