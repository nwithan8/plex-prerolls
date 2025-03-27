import textwrap
from typing import Union, Tuple

import ffmpeg
import requests
from plexapi.video import Movie

import modules.logs as logging
from consts import ASSETS_DIR, AUTO_GENERATED_RECENTLY_ADDED_PREROLL_PREFIX
from modules import youtube_downloader as ytd, utils, ffmpeg_utils
from modules.renderers.base import PrerollRenderer
from modules.config_parser import Config

LENGTH_SECONDS = 33.5


def _trim_background_music(background_music_file_path: str) -> str:
    logging.info(f"Trimming {background_music_file_path} to {LENGTH_SECONDS} seconds")
    video_file_path = ffmpeg_utils.trim_audio_file_to_length(audio_file_path=background_music_file_path,
                                                             length_seconds=LENGTH_SECONDS,
                                                             fade_in=True,
                                                             fade_in_length=0.5,
                                                             fade_out=True,
                                                             fade_out_length=2)
    logging.info(f"Converting {video_file_path} to MP3")
    audio_file_path = f"{video_file_path.split('.')[0]}.mp3"
    ffmpeg_utils.convert_video_to_audio(video_file_path=video_file_path, audio_file_path=audio_file_path)

    return audio_file_path


class RecentlyAddedPrerollRenderer(PrerollRenderer):
    def __init__(self, render_folder: str, movie: Movie):
        super().__init__()
        self.download_folder = render_folder  # Will be set in render()
        self._video_file_name = "video"
        self._audio_file_name = "audio"
        self._poster_file_name = "poster.jpg"
        # Needs to end with epoch timestamp to sort correctly during rclone sync
        self._output_file_name = f"{AUTO_GENERATED_RECENTLY_ADDED_PREROLL_PREFIX}-{utils.now_epoch()}.mp4"
        self.movie_title = movie.title
        self.movie_year = getattr(movie, "year", None)
        duration_milliseconds = getattr(movie, "duration", 0)
        self.movie_duration_human = utils.milliseconds_to_hours_minutes_seconds(milliseconds=duration_milliseconds)
        self.movie_tagline = getattr(movie, "tagline", "")
        self.movie_summary = getattr(movie, "summary", "")
        self.movie_studio = getattr(movie, "studio", "")
        self.movie_directors = getattr(movie, "directors", [])
        self.movie_actors = getattr(movie, "actors", [])
        self.movie_genres = getattr(movie, "genres", [])
        self.movie_critic_rating = getattr(movie, "rating", None)  # 0.0 - 10.0
        self.movie_audience_rating = getattr(movie, "audienceRating", None)  # 0.0 - 10.0
        self.movie_poster_url = getattr(movie, "posterUrl", None)

    @property
    def youtube_search_query_movie_title(self) -> str:
        return f'"{self.movie_title}" {self.movie_year or ""}'.strip()

    def _get_trailer(self, config: Config) -> str:
        search_query = f"{self.youtube_search_query_movie_title} Official Movie Theatrical Trailer"
        logging.info(f'Retrieving trailer for "{self.movie_title}", YouTube search query: "{search_query}"')
        video_id = ytd.run_youtube_search(
            query=f"{self.youtube_search_query_movie_title} Official Movie Theatrical Trailer",
            selector_function=ytd.SelectorPresets.select_first_video,
            results_limit=5)
        video_url = ytd.get_video_url(video_id=video_id)
        video_file_path = ytd.download_youtube_video(config,
                                                     url=video_url,
                                                     output_dir=self.download_folder,
                                                     output_filename=self._video_file_name)
        logging.info("Trailer retrieved successfully")
        return video_file_path

    def _get_background_music(self) -> str:
        search_query = f"{self.youtube_search_query_movie_title} movie soundtrack"
        logging.info(f'Retrieving background music for "{self.movie_title}", YouTube search query: "{search_query}"')
        video_id = ytd.run_youtube_search(query=f"{self.youtube_search_query_movie_title} movie soundtrack",
                                          selector_function=ytd.SelectorPresets.select_first_video,
                                          results_limit=5)
        video_url = ytd.get_video_url(video_id=video_id)
        video_file_path = ytd.download_youtube_video(config,
                                                     url=video_url,
                                                     output_dir=self.download_folder,
                                                     output_filename=self._audio_file_name)
        logging.info("Background music retrieved successfully")
        return video_file_path

    def _get_movie_poster(self) -> Union[str, None]:
        logging.info(f'Retrieving poster for "{self.movie_title}"')
        if not self.movie_poster_url:
            logging.warning(f"No poster URL available for {self.movie_title}")
            return None
        res = requests.get(self.movie_poster_url)
        file_path = f"{self.download_folder}/{self._poster_file_name}"
        with open(file_path, "wb") as f:
            f.write(res.content)

        logging.info("Poster retrieved successfully")
        return file_path

    def render(self, config: Config) -> Tuple[Union[str, None], Union[str, None]]:
        if not self.movie_title:
            logging.warning("No movie title available, cannot build preroll")
            return None, None
        if not self.movie_year:
            logging.warning("No movie year available, not going to attempt to build preroll")
            return None, None
        trailer_cutoff_year = config.advanced.auto_generation.recently_added.trailer_cutoff_year
        if self.movie_year < trailer_cutoff_year:
            # Finding good trailers automatically for movies older than 1980 is difficult (year is arbitrary)
            logging.warning("Movie is too old, not going to attempt to build preroll")
            return None, None

        self.download_folder = utils.get_temporary_directory_path(parent_directory=self.download_folder)
        logging.info(f'Retrieving assets for preroll of "{self.movie_title}", saving to {self.download_folder}')
        video_path = self._get_trailer(config)
        audio_path = self._get_background_music(config)
        audio_path = _trim_background_music(background_music_file_path=audio_path)
        poster_path = self._get_movie_poster()

        logging.info(f'Rendering preroll for "{self.movie_title}"')
        title_position_offset = (len(self.movie_title) * 33) / 2 - 7
        if title_position_offset > 716:
            title = textwrap.fill(self.movie_title, width=40, break_long_words=False)
            title_newline = title.find("\n")
            title_position_offset = (title_newline * 33) / 2 - 7

        description = textwrap.fill(self.movie_summary, width=22, break_long_words=False)
        num_of_lines = description.count("\n")
        description_size = 580 / num_of_lines if num_of_lines > 22 else 26

        # Prepare elements for preroll video
        sidebar = ffmpeg.input(f"{ASSETS_DIR}/overlay.mov")
        poster = ffmpeg.filter(ffmpeg.input(poster_path, loop=1), "scale", 200, -1)
        fade_out = ffmpeg.input(f"{ASSETS_DIR}/fade_out.mov")
        title_font = f"{ASSETS_DIR}/Bebas-Regular.ttf"
        description_font = f"{ASSETS_DIR}/Roboto-Light.ttf"

        # Prepare preroll video
        ffmpeg_command = ffmpeg.input(video_path, ss=10, t=LENGTH_SECONDS)
        ffmpeg_command = ffmpeg.filter(ffmpeg_command, "scale", 1600, -1)
        ffmpeg_audio_command = ffmpeg.input(audio_path)
        ffmpeg_command = ffmpeg.overlay(sidebar, ffmpeg_command, x=300, y=125)
        ffmpeg_command = ffmpeg.overlay(ffmpeg_command, poster, x=40, y=195, enable="gte(t,1)")

        # Add ratings
        # If neither rating is available, show nothing
        if not self.movie_critic_rating and not self.movie_audience_rating:
            pass
        # If both ratings are available, show both
        elif self.movie_critic_rating and self.movie_audience_rating:
            ffmpeg_command = ffmpeg.drawtext(
                ffmpeg_command,
                text=f"Critic Rating: {self.movie_critic_rating}",
                fontfile=title_font,
                x=3,
                y=135,
                escape_text=True,
                fontcolor="0xFFFFFF@0xff",
                fontsize=32,
                enable="gte(t,1)",
            )
            ffmpeg_command = ffmpeg.drawtext(
                ffmpeg_command,
                text=f"Audience Rating: {self.movie_audience_rating}",
                fontfile=title_font,
                x=3,
                y=165,
                escape_text=True,
                fontcolor="0xFFFFFF@0xff",
                fontsize=32,
                enable="gte(t,1)",
            )
        # If only one rating is available, show that one
        else:
            rating = self.movie_critic_rating or self.movie_audience_rating
            rating_type = "Critic" if self.movie_critic_rating else "Audience"
            ffmpeg_command = ffmpeg.drawtext(
                ffmpeg_command,
                text=f"{rating_type} Rating: {rating}",
                fontfile=title_font,
                x=3,
                y=150,
                escape_text=True,
                fontcolor="0xFFFFFF@0xff",
                fontsize=36,
                enable="gte(t,1)",
            )

        # Add title and description
        ffmpeg_command = ffmpeg.drawtext(
            ffmpeg_command,
            text=self.movie_title,
            fontfile=title_font,
            x=(1106 - title_position_offset),
            y=20,
            escape_text=True,
            fontcolor="0xFFFFFF@0xff",
            fontsize=76,
            enable="gte(t,1)",
        )
        ffmpeg_command = ffmpeg.drawtext(
            ffmpeg_command,
            text=description,
            fontfile=description_font,
            x=3,
            y=500,
            escape_text=True,
            fontcolor="0xFFFFFF@0xff",
            fontsize=description_size,
            enable="gte(t,1)",
        )

        # TODO: Add studio, directors, actors, genres, tagline

        # Add fade out
        ffmpeg_command = ffmpeg.overlay(ffmpeg_command, fade_out, eof_action="endall")

        # Combine video and audio
        file_path = f"{self.download_folder}/{self._output_file_name}"
        ffmpeg_command = ffmpeg.output(ffmpeg_audio_command, ffmpeg_command,
                                       file_path, )

        # Run ffmpeg command
        ffmpeg.run(ffmpeg_command, overwrite_output=True, quiet=False)

        logging.info(f'Preroll for "{self.movie_title}" rendered successfully to {file_path}')

        return self.download_folder, file_path
