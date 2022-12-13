from .options import Options


class Synchronizer:
    def __init__(self, urls: tuple[str], options: Options):
        self._urls = urls
        self._options = options

    def run(self):
        print(self._urls)
        print(self._options)
