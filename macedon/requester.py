import threading as t


class Requester(t.Thread):
    def __init__(self, urls: list[str]):
        self._urls = urls
        super().__init__()

    def run(self):
        pass
