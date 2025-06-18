from typing import Callable

from modules import youtube_downloader as ytd
from modules.config_parser import Config


class PrerollRenderer:
    def __init__(self):
        pass

    def render(self, config: Config):
        raise NotImplementedError
