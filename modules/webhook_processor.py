from typing import Union

from flask import (
    jsonify,
    request as flask_request,
)

from modules.config_parser import Config


class WebhookProcessor:
    def __init__(self):
        pass

    @staticmethod
    def process_ping(request: flask_request, config: Config) -> [Union[str, None], int]:
        """
        Process a ping request.
        Return a 'Pong!' response and a 200 status code.
        """
        return 'Pong!', 200

    @staticmethod
    def process_recently_added(request: flask_request, config: Config) -> [Union[str, None], int]:
        """
        Process a recently added webhook from Tautulli.
        """
        return jsonify({}), 200
