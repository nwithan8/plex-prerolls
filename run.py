import argparse

import modules.logs as logging
from consts import (
    APP_NAME,
    APP_DESCRIPTION,
    DEFAULT_CONFIG_PATH,
    DEFAULT_LOG_DIR,
    CONSOLE_LOG_LEVEL,
    FILE_LOG_LEVEL,
)
from modules.config_parser import Config
from modules.plex_connector import PlexConnector
from modules.schedule_manager import ScheduleManager

parser = argparse.ArgumentParser(description=f"{APP_NAME} - {APP_DESCRIPTION}")

parser.add_argument("-c", "--config", help=f"Path to config file. Defaults to '{DEFAULT_CONFIG_PATH}'",
                    default=DEFAULT_CONFIG_PATH)

# Should include trailing backslash
parser.add_argument("-l", "--log", help=f"Log file directory. Defaults to '{DEFAULT_LOG_DIR}'", default=DEFAULT_LOG_DIR)

parser.add_argument("-d", "--dry-run", help="Dry run, no real changes made", action="store_true")

args = parser.parse_args()

# Set up logging
logging.init(app_name=APP_NAME, console_log_level=FILE_LOG_LEVEL if args.dry_run else CONSOLE_LOG_LEVEL, log_to_file=True, log_file_dir=args.log,
             file_log_level=FILE_LOG_LEVEL)

config = Config(app_name=APP_NAME, config_path=f"{args.config}")

if __name__ == '__main__':
    # logging.info(splash_logo())
    logging.info(f"Starting {APP_NAME}...")

    schedule_manager = ScheduleManager(config=config)

    logging.info(f"Found {schedule_manager.valid_schedule_count} valid schedules")
    logging.info(schedule_manager.valid_schedule_count_log_message)

    all_valid_paths = schedule_manager.all_valid_paths

    plex_connector = PlexConnector(host=config.plex.url, token=config.plex.token)
    plex_connector.update_pre_roll_paths(paths=all_valid_paths, testing=args.dry_run)
