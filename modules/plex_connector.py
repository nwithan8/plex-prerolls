from typing import List, Union

from plexapi.server import PlexServer

import modules.logs as logging


def prepare_pre_roll_string(paths: List[str]) -> Union[str, None]:
    if not paths:
        return None

    # Filter out empty paths
    paths = [path for path in paths if path]

    return ";".join(paths)


class PlexConnector:
    def __init__(self, host: str, token: str):
        self._host = host
        self._token = token
        logging.info(f"Connecting to Plex server at {self._host}")
        self._plex_server = PlexServer(baseurl=self._host, token=self._token)

    def update_pre_roll_paths(self, paths: List[str], testing: bool = False) -> None:
        pre_roll_string = prepare_pre_roll_string(paths=paths)
        if not pre_roll_string:
            logging.info("No pre-roll paths to update")
            return

        if testing:
            logging.debug(f"Testing: Would have updated pre-roll to: {pre_roll_string}")
            return

        logging.info(f"Updating pre-roll to: {pre_roll_string}")

        self._plex_server.settings.get("cinemaTrailersPrerollID").set(pre_roll_string)  # type: ignore

        try:
            self._plex_server.settings.save()  # type: ignore
        except Exception as e:
            logging.error(f"Failed to save pre-roll: {e}")
            return

        logging.info("Successfully updated pre-roll")
