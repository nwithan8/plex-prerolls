import argparse
from flask import (
    Flask,
    request as flask_request,
)

import modules.logs as logging
from consts import (
    APP_NAME,
    APP_DESCRIPTION,
    DEFAULT_CONFIG_PATH,
    DEFAULT_LOG_DIR,
    DEFAULT_RENDERS_DIR,
    CONSOLE_LOG_LEVEL,
    FILE_LOG_LEVEL,
    FLASK_ADDRESS,
    FLASK_PORT,
)
from modules.config_parser import Config
from modules.errors import determine_exit_code
from modules.webhooks.webhook_processor import WebhookProcessor

parser = argparse.ArgumentParser(description=f"{APP_NAME} - {APP_DESCRIPTION}")

parser.add_argument("-c", "--config", help=f"Path to config file. Defaults to '{DEFAULT_CONFIG_PATH}'",
                    default=DEFAULT_CONFIG_PATH)
parser.add_argument("-l", "--log", help=f"Log file directory. Defaults to '{DEFAULT_LOG_DIR}'",
                    default=DEFAULT_LOG_DIR)  # Should include trailing backslash
parser.add_argument("-r", "--renders", help=f"Path to renders directory. Defaults to '{DEFAULT_RENDERS_DIR}'",
                    default=DEFAULT_RENDERS_DIR)
args = parser.parse_args()

# Set up logging
logging.init(app_name=APP_NAME,
             console_log_level=CONSOLE_LOG_LEVEL,
             log_to_file=True,
             log_file_dir=args.log,
             file_log_level=FILE_LOG_LEVEL)

_config = Config(app_name=APP_NAME, config_path=f"{args.config}")


def run_with_potential_exit_on_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.fatal(f"Fatal error occurred. Shutting down: {e}")
            exit_code = determine_exit_code(exception=e)
            logging.fatal(f"Exiting with code {exit_code}")
            exit(exit_code)

    return wrapper

@run_with_potential_exit_on_error
def start_webhooks_server(config: Config) -> None:
    api = Flask(APP_NAME)

    @api.route('/ping', methods=['GET'])
    def ping():
        return WebhookProcessor.process_ping(request=flask_request, config=config)

    @api.route('/recently-added', methods=['POST'])
    def recently_added():
        if not config.advanced.auto_generation.recently_added.enabled:
            return 'Recently added preroll generation is disabled', 200
        return WebhookProcessor.process_recently_added(request=flask_request, config=config, output_dir=args.renders)

    @api.route('/last-run-within', methods=['GET'])
    def last_run_within():
        return WebhookProcessor.process_last_run_within(request=flask_request, logs_folder=args.log)

    api.run(host=FLASK_ADDRESS, port=FLASK_PORT, debug=True, use_reloader=False)


if __name__ == "__main__":
    start_webhooks_server(config=_config)
