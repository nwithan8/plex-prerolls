#!/usr/bin/python
"""Plex config parsing utilities

Raises:
    FileNotFoundError: [description]
    KeyError: [description]
"""
import logging
import logging.config
import os
import sys
from configparser import ConfigParser
from typing import Dict, Optional

from plexapi.server import CONFIG  # type: ignore

logger = logging.getLogger(__name__)

filename = os.path.basename(sys.argv[0])
SCRIPT_NAME = os.path.splitext(filename)[0]


def plex_config(config_file: Optional[str] = "") -> Dict[str, str]:
    """Return Plex Config parameters for connection info {PLEX_URL, PLEX_TOKEN}\n
    Attempts to use one of either:\n
    * supplier path/to/config file (INI Format)
    * local config.ini (primary)
    * PlexAPI system config.ini (secondary)

    Args:
        config_file (str): path/to/config.ini style config file (INI Format)

    Raises:
        KeyError: Config Params not found in config file(s)
        FileNotFoundError: Cannot find a config file

    Returns:
        dict: Dict of config params {PLEX_URL, PLEX_TOKEN}
    """

    cfg: dict[str, str] = {}
    plex_url = ""
    plex_token = ""
    filename = ""
    use_local_config = False
    use_plexapi_config = False

    # Look for a local Config.ini file, use settings if present
    local_config = ConfigParser()

    if config_file == None or config_file == "":
        filename = "config.ini"
    else:
        filename = str(config_file)

    # try reading a local file
    local_config.read(filename)

    if len(local_config.sections()) > 0:  # len(found_config) > 0:
        # if local config.ini file found, try to use local first
        if local_config.has_section("auth"):
            try:
                server = local_config["auth"]
                plex_url = server["server_baseurl"]
                plex_token = server["server_token"]

                if len(plex_url) > 1 and len(plex_token) > 1:
                    use_local_config = True
            except KeyError as e:
                logger.error("Key Value not found", exc_info=e)
                raise e
        else:
            msg = "[auth] section not found in LOCAL config.ini file"
            logger.error(msg)
            raise KeyError(msg)

    if not use_local_config and len(CONFIG.sections()) > 0:  # type: ignore
        # use PlexAPI Default ~/.config/plexapi/config.ini OR from PLEXAPI_CONFIG_PATH
        # IF not manually set locally in local Config.ini above
        # See https://python-plexapi.readthedocs.io/en/latest/configuration.html
        if CONFIG.has_section("auth"):  # type: ignore
            try:
                server = CONFIG.data["auth"]  # type: ignore
                plex_url: str = server.get("server_baseurl")  # type: ignore
                plex_token: str = server.get("server_token")  # type: ignore

                if len(plex_url) > 1 and len(plex_token) > 1:
                    use_plexapi_config = True
            except KeyError as e:
                logger.error("Key Value not found", exc_info=e)
                raise e
        else:
            msg = "[auth] section not found in PlexAPI MAIN config.ini file"
            logger.error(msg)
            raise KeyError(msg)

    if not use_local_config and not use_plexapi_config:
        msg = "ConfigFile Error: No Plex config information found [server_baseurl, server_token]"
        logger.error(msg)
        raise FileNotFoundError(msg)

    cfg["PLEX_URL"] = plex_url
    cfg["PLEX_TOKEN"] = plex_token

    return cfg


def init_logger(log_config: str) -> None:
    """load and configure a program logger using a supplier logging configuration file \n
    if possible the program will attempt to create log folders if not already existing

    Args:
        log_config (str): path/to/logging.(conf|ini) style config file (INI Format)

    Raises:
        KeyError: Problems processing logging config files
        FileNotFoundError: Problems with log file location, other
    """

    if os.path.exists(log_config):
        try:
            logging.config.fileConfig(log_config, disable_existing_loggers=False)
        except FileNotFoundError as e_fnf:
            # Assume this is related to a missing Log Folder
            # Try to create
            if e_fnf.filename and e_fnf.filename[-3:] == "log":
                logfile = e_fnf.filename
                logdir = os.path.dirname(logfile)

                if not os.path.exists(logdir):
                    try:
                        logger.debug('Creating log folder "%s"', logdir)
                        os.makedirs(logdir, exist_ok=True)
                    except Exception as e:
                        logger.error('Error creating log folder "%s"', logdir, exc_info=e)
                        raise e
            elif logger.handlers:
                # if logger config loaded, but some file error happened
                for h in logger.handlers:
                    if isinstance(h, logging.FileHandler):
                        logfile = h.baseFilename
                        logdir = os.path.dirname(logfile)

                        if not os.path.exists(logdir):
                            try:
                                logger.debug('Creating log folder "%s"', logdir)

                                os.makedirs(logdir, exist_ok=True)
                            except Exception as e:
                                logger.error('Error creating log folder "%s"', logdir, exc_info=e)
                                raise e
            else:
                # not sure the issue, raise the exception
                raise e_fnf

            # Assuming one of the create Log Folder worked, try again
            logging.config.fileConfig(log_config, disable_existing_loggers=False)

    else:
        logger.debug('Logging Config file "%s" not available, will be using defaults', log_config)


if __name__ == "__main__":
    msg = (
        "Script not meant to be run directly, please import into other scripts.\n\n"
        + f"usage:\nimport {SCRIPT_NAME}"
        + "\n"
        + f"cfg = {SCRIPT_NAME}.getPlexConfig()"
        + "\n"
    )
    logger.error(msg)
