import argparse
import threading
from datetime import datetime
from time import sleep

from croniter import croniter
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
from modules.plex_connector import PlexConnector
from modules.schedule_manager import ScheduleManager
from modules.webhooks.webhook_processor import WebhookProcessor

parser = argparse.ArgumentParser(description=f"{APP_NAME} - {APP_DESCRIPTION}")

parser.add_argument("-c", "--config", help=f"Path to config file. Defaults to '{DEFAULT_CONFIG_PATH}'",
                    default=DEFAULT_CONFIG_PATH)
parser.add_argument("-l", "--log", help=f"Log file directory. Defaults to '{DEFAULT_LOG_DIR}'",
                    default=DEFAULT_LOG_DIR)  # Should include trailing backslash
parser.add_argument("-r", "--renders", help=f"Path to renders directory. Defaults to '{DEFAULT_RENDERS_DIR}'",
                    default=DEFAULT_RENDERS_DIR)
parser.add_argument("-s", "--schedule", help="Cron pattern for pre-roll update", default="0 0 * * *")
parser.add_argument("-d", "--dry-run", help="Dry run, no real changes made", action="store_true")

args = parser.parse_args()

# Set up logging
logging.init(app_name=APP_NAME, console_log_level=FILE_LOG_LEVEL if args.dry_run else CONSOLE_LOG_LEVEL,
             log_to_file=True, log_file_dir=args.log,
             file_log_level=FILE_LOG_LEVEL)

_config = Config(app_name=APP_NAME, config_path=f"{args.config}")


def run_with_potential_exit_on_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.fatal(f"Fatal error occurred. Shutting down: {e}")
            exit_code = 1
            logging.fatal(f"Exiting with code {exit_code}")
            exit(exit_code)

    return wrapper


def start_webhooks_server(config: Config) -> [Flask, threading.Thread]:
    api = Flask(APP_NAME)

    @api.route('/ping', methods=['GET'])
    def ping():
        return WebhookProcessor.process_ping(request=flask_request, config=config)

    @api.route('/recently-added', methods=['POST'])
    def recently_added():
        return WebhookProcessor.process_recently_added(request=flask_request, config=config, output_dir=args.renders)

    flask_thread = threading.Thread(
        target=lambda: api.run(host=FLASK_ADDRESS, port=FLASK_PORT, debug=True, use_reloader=False))
    logging.info("Starting Flask server")
    flask_thread.start()

    return api, flask_thread


def start_pre_roll_cronjob(config: Config):
    updater_thread = threading.Thread(
        target=lambda: pre_roll_update(cron_pattern=args.schedule, config=config))
    logging.info(f"Starting pre-roll update cronjob...")
    updater_thread.start()

    return updater_thread


def pre_roll_update(cron_pattern: str, config: Config):
    while True:
        now = datetime.now()
        if not croniter.match(cron_pattern, now):
            # Cron only goes to minutes, not seconds, so we don't need to recheck as often
            sleep(30)  # Sleep/check every 30 seconds
            continue

        logging.info(f"Current time {now} matches cron pattern '{cron_pattern}'")
        logging.info(f"Running pre-roll update...")

        schedule_manager = ScheduleManager(config=config)

        logging.info(f"Found {schedule_manager.valid_schedule_count} valid schedules")
        logging.info(schedule_manager.valid_schedule_count_log_message)

        all_valid_paths = schedule_manager.all_valid_paths

        plex_connector = PlexConnector(host=config.plex.url, token=config.plex.token)
        # plex_connector.update_pre_roll_paths(paths=all_valid_paths, testing=args.dry_run)

        sleep(60)  # Sleep at least a minute to avoid running multiple times in the same minute


if __name__ == '__main__':
    # logging.info(splash_logo())
    logging.info(f"Starting {APP_NAME}...")

    _api, _flask_thread = start_webhooks_server(config=_config)
    # _updater_thread = start_pre_roll_cronjob(config=_config)
