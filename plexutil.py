#!/usr/bin/python
"""Plex config parsing utilities

Raises:
    FileNotFoundError: [description]
    KeyError: [description]
    KeyError: [description]
    ConfigError: [description]
"""
import os
import sys
import logging
from configparser import ConfigParser
from plexapi.server import PlexServer, CONFIG

logger = logging.getLogger(__name__)

filename = os.path.basename(sys.argv[0])
SCRIPT_NAME = os.path.splitext(filename)[0]

def getPlexConfig(config_file=None):
    """Return Plex Config paramaters for connection info {PLEX_URL, PLEX_TOKEN}\n
    Attempts to use either a local config.ini (primary) as well as a PlexAPI system config.ini (secondary)

    Raises:
        KeyError: Config Params not found in config file(s)
        FileNotFoundError: If cannot find a config file

    Returns:
        dict: Dict of config params {PLEX_URL, PLEX_TOKEN}
    """
    cfg = {}
    plex_url = ''
    plex_token = ''
    use_local_config = False
    use_plexapi_config = False

    # Look for a local Config.ini file, use settings if present
    local_config = ConfigParser()

    if config_file != None:
        if os.path.exists(config_file):
           filename = config_file
        else:
            raise FileNotFoundError('Config file -c "{}" not found'.format(config_file))
    else:
        filename = 'config.ini'

    #try reading a local file
    local_config.read(filename)

    if len(local_config.sections()) > 0:  #len(found_config) > 0:
        # if local config.ini file found, try to use local first
        if local_config.has_section('auth'):
            try: 
                server = local_config['auth']
                plex_url = server['server_baseurl']
                plex_token = server['server_token']

                if len(plex_url) > 1 and len(plex_token) > 1:
                    use_local_config = True
            except KeyError as e:
                logger.error('Key Value not found {}', exc_info=e)
                raise e
        else:
            msg = '[auth] section not found in LOCAL config.ini file'
            logger.error(msg)
            raise KeyError(msg)

    if not use_local_config and len(CONFIG.sections()) > 0:
        # use PlexAPI Default ~/.config/plexapi/config.ini OR from PLEXAPI_CONFIG_PATH
        # IF not manually set locally in local Config.ini above
        # See https://python-plexapi.readthedocs.io/en/latest/configuration.html
        if CONFIG.has_section('auth'):
            try:
                server = CONFIG.data['auth']
                plex_url = server.get('server_baseurl')
                plex_token = server.get('server_token')

                if len(plex_url) > 1 and len(plex_token) > 1:
                    use_plexapi_config = True
            except KeyError as e:
                logger.error('Key Value not found', exc_info=e)
                raise e
        else:
            msg = "[auth] section not found in PlexAPI MAIN config.ini file"
            logger.error(msg)
            raise KeyError(msg)

    if not use_local_config and not use_plexapi_config:
        msg = 'No Plex config information found {server_baseurl, server_token}'
        logger.error(msg)
        raise ConfigError(msg) 

    cfg['PLEX_URL'] = plex_url
    cfg['PLEX_TOKEN']= plex_token

    return cfg

if __name__ == '__main__':
    msg = 'Script not meant to be run directly, please import into other scripts.\n\n' + \
           'usage:\nimport {}'.format(SCRIPT_NAME) + '\n' + \
           'cfg = {}.getPlexConfig()'.format(SCRIPT_NAME) + '\n'
    logger.error(msg)