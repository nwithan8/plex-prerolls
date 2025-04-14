import json
import threading
from typing import Union

import pydantic_core
from flask import (
    jsonify,
    request as flask_request,
)
from plexapi.video import Movie

import modules.logs as logging
from modules import utils
from modules.config_parser import Config
from modules.plex_connector import PlexConnector
from modules.renderers import RecentlyAddedPrerollRenderer
from modules.webhooks.plex import PlexWebhook, PlexWebhookEventType, PlexWebhookMetadataType


class WebhookProcessor:
    def __init__(self):
        pass

    @classmethod
    def _extract_body(cls, request: flask_request) -> dict:
        """
        Extract the body from a Flask request.
        """
        try:
            form_data = request.form.get('payload', '{}')
            return json.loads(form_data)
        except Exception as e:
            return {}

    @staticmethod
    def process_ping(request: flask_request, config: Config) -> [Union[str, None], int]:
        """
        Process a ping request.
        Return a 'Pong!' response and a 200 status code.
        """
        return 'Pong!', 200

    @staticmethod
    def process_recently_added(request: flask_request, config: Config, output_dir: str) -> [Union[str, None], int]:
        """
        Process a recently added webhook from Tautulli.
        """
        json_data = WebhookProcessor._extract_body(request=request)

        try:
            webhook = PlexWebhook(**json_data)
        except pydantic_core._pydantic_core.ValidationError as e:
            # If we receive a validation error (incoming webhook does not have the payload we expect), simply ignore it
            # This can happen, e.g. when we receive a playback start webhook for a cinema trailer, which does not have a librarySectionID
            return jsonify({}), 200

        match webhook.event_type:
            case PlexWebhookEventType.MEDIA_ADDED:
                if webhook.metadata.type == PlexWebhookMetadataType.MOVIE.value:  # Skip if new content is not a movie
                    thread = threading.Thread(target=WebhookProcessor._process_recently_added_preroll_render,
                                              args=(webhook, config, output_dir))
                    thread.start()
            case _:  # pragma: no cover
                pass

        return jsonify({}), 200

    @staticmethod
    def _process_recently_added_preroll_render(webhook: PlexWebhook, config: Config, output_dir: str) -> None:
        """
        Process the preroll render for a recently added webhook.
        """
        plex_connector = PlexConnector(host=config.plex.url, token=config.plex.token)
        logging.info(f'Retrieving information from Plex for recently added movie: "{webhook.metadata.title}"')
        plex_movie: Movie = plex_connector.get_movie(item_key=webhook.metadata.key)
        if not plex_movie:
            logging.warning(f'Could not find movie in Plex: "{webhook.metadata.title}"')  # Not an error, just a warning
            return

        renderer = RecentlyAddedPrerollRenderer(render_folder=output_dir,
                                                movie=plex_movie)
        asset_folder, local_file_path = renderer.render(config=config)

        if not local_file_path:  # error has already been logged
            return

        destination_folder = f"{config.advanced.auto_generation.recently_added.local_files_root}"
        utils.create_directory(directory=destination_folder)
        utils.copy_file(source=local_file_path, destination=destination_folder)

        files_to_delete = utils.get_all_files_in_directory_beyond_most_recent_x_count(directory=destination_folder,
                                                                                      count=config.advanced.auto_generation.recently_added.count)
        logging.info(
            f"Deleting {len(files_to_delete)} prerolls from {destination_folder} to maintain {config.advanced.auto_generation.recently_added.count} auto-generated prerolls limit")
        for remote_file in files_to_delete:
            utils.delete_file(remote_file)

        logging.info(f"Cleaning up local preroll assets folder: '{asset_folder}'")
        utils.delete_directory(directory=asset_folder)
