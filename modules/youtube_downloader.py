from typing import Callable

import youtubesearchpython
import yt_dlp
import os

import modules.logs as logging
from modules.config_parser import Config


class SelectorPresets:
    @staticmethod
    def select_first_video(videos: dict) -> str:
        """
        Select the first video ID from a search result.

        :param videos: The search result dictionary.

        :return: The selected video ID.
        """
        return videos[0]['id']

    @staticmethod
    def select_last_video(videos: dict) -> str:
        """
        Select the last video ID from a search result.

        :param videos: The search result dictionary.

        :return: The selected video ID.
        """
        return videos[-1]['id']

    @staticmethod
    def select_random_video(videos: dict) -> str:
        """
        Select a random video ID from a search result.

        :param videos: The search result dictionary.

        :return: The selected video ID.
        """
        import random
        return random.choice(videos)['id']


class YouTubeDownloaderLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
        if msg.startswith('[debug] '):
            pass  # Suppress debug messages
            # logging.debug(msg)
        else:
            self.info(msg)

    def info(self, msg):
        pass  # Suppress info messages
        # logging.info(msg)

    def warning(self, msg):
        logging.warning(msg)

    def error(self, msg):
        logging.error(msg)


def _download_progress_hook(d):
    if d['status'] == 'finished':
        logging.info('Download complete')


def get_video_url(video_id: str) -> str:
    """
    Get a YouTube video URL from a video ID.

    :param video_id: The video ID.

    :return: The video URL.
    """
    return f"https://www.youtube.com/watch?v={video_id}"


def run_youtube_search(query: str, selector_function: Callable[[dict], str], results_limit: int = 20) -> str:
    """
    Run a YouTube search and return a video ID.

    :param query: The search query.
    :param selector_function: A function that selects a video ID from the search results dictionary.
    :param results_limit: The number of results to return.

    :return: The selected video ID.
    """
    search_results: dict = youtubesearchpython.CustomSearch(query=query,
                                                            # sp parameter: Videos only, <4 minutes, sorted by relevance
                                                            searchPreferences="EgQQARgB",
                                                            limit=results_limit).result()
    videos = search_results['result']
    return selector_function(videos)


def download_youtube_video(url: str, config: Config, output_dir: str, output_filename: str = None) -> str:
    """
    Download a YouTube video as a video file.

    :param url: The YouTube video URL.
    :param config: The configuration for Plex Prerolls.
    :param output_dir: The output directory.
    :param output_filename: The output filename.
    :return: The path to the downloaded file.
    """
    cookies_file = config.advanced.auto_generation.cookies_file
    options = {
        "paths": {"home": output_dir},
        'logger': YouTubeDownloaderLogger(),
        # 'progress_hooks': [_download_progress_hook],
        "overwrites": True,
    }
    if output_filename:
        options['outtmpl'] = f"{output_filename}.%(ext)s"
    if cookies_file:
        options['cookiefile'] = cookies_file

    with yt_dlp.YoutubeDL(params=options) as ydl:
        # download the file and extract info
        info = ydl.extract_info(url, download=True)
        # return the file path
        return ydl.prepare_filename(info)


def download_youtube_audio(url: str, config: Config, output_dir: str, output_filename: str = None) -> str:
    """
    Download a YouTube video as an audio file.

    :param url: The YouTube video URL.
    :param config: The configuration for Plex Prerolls.
    :param output_dir: The output directory.
    :param output_filename: The output filename.
    :return: The path to the downloaded file.
    """
    cookies_file = config.advanced.auto_generation.cookies_file
    options = {
        "paths": {"home": output_dir},
        'format': 'm4a/bestaudio/best',
        'postprocessors': [{  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
        }],
        'logger': YouTubeDownloaderLogger(),
        # 'progress_hooks': [_download_progress_hook],
        "overwrites": True,
    }
    if output_filename:
        options['outtmpl'] = f"{output_filename}.%(ext)s"
    if cookies_file:
        options['cookiefile'] = cookies_file

    with yt_dlp.YoutubeDL(params=options) as ydl:
        # download the file and extract info
        info = ydl.extract_info(url, download=True)
        # return the file path
        return ydl.prepare_filename(info)
