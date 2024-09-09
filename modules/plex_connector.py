from typing import List, Union, Tuple

from plexapi.exceptions import BadRequest
from plexapi.server import PlexServer
from plexapi.video import Movie

import modules.logs as logging


def prepare_pre_roll_string(paths: List[str]) -> Tuple[Union[str, None], int]:
    if not paths:
        return None, 0

    # Filter out empty paths
    paths = [path for path in paths if path]

    return ";".join(paths), len(paths)


class PlexConnector:
    def __init__(self, host: str, token: str):
        self._host = host
        self._token = token
        logging.info(f"Connecting to Plex server at {self._host}")
        self._plex_server = PlexServer(baseurl=self._host, token=self._token)

    def update_pre_roll_paths(self, paths: List[str], testing: bool = False) -> None:
        pre_roll_string, count = prepare_pre_roll_string(paths=paths)
        if not pre_roll_string:
            logging.info("No pre-roll paths to update")
            return

        logging.info(f"Using {count} pre-roll paths")

        if testing:
            logging.debug(f"Testing: Would have updated pre-roll to: {pre_roll_string}")
            return

        logging.info(f"Updating pre-roll to: {pre_roll_string}")

        self._plex_server.settings.get("cinemaTrailersPrerollID").set(pre_roll_string)  # type: ignore

        try:
            self._plex_server.settings.save()  # type: ignore
        except BadRequest as e:
            if "Too Large" in str(e):
                logging.error("Failed to update pre-roll: Too many paths")
                return
        except Exception as e:
            logging.error(f"Failed to save pre-roll: {e}")
            return

        logging.info("Successfully updated pre-roll")

    def get_movie(self, item_key: str) -> Union[None, Movie]:
        """
        Get a movie from the Plex server

        :param item_key: The key of the movie, should start with "/library/metadata/"
        :return: The movie object or None
        """
        try:
            return self._plex_server.fetchItem(ekey=item_key)
        except Exception as e:
            logging.error(f"Failed to get movie: {e}")
            return None
