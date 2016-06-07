from abc import ABC, abstractmethod


class Extractor(ABC):
    def __init__(self, media):
        self.media = media
        self.links = []

    @abstractmethod
    def search(self):
        pass
