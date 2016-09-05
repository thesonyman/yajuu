import subprocess
import json


class FFProbe:

	"""Simple wrapper arround the ffprobe json api."""

	def __init__(self, url):
		command = [
			'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format',
			'-show_streams', url
		]

		process = subprocess.Popen(command, stdout=subprocess.PIPE)
		out = process.communicate()[0]

		self._raw = json.loads(out.decode('utf-8'))

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
