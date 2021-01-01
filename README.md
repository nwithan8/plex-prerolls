# Schedule Plex server related Pre-roll intro videos

A helper script to automate management of Plex pre-rolls. \
Define when you want different pre-rolls to play throughout the year.

Ideas include:

- Holiday pre-roll rotations
- Special occasions
- Summer/Winter rotations
- Breaking up the monotony
- Keeping your family/friends on their toes!

Set it and forget it!

---
## Installation & Setup <a id="install"></a>

Grab a copy of the code

```sh
cd /path/to/your/location
git clone https://github.com/BrianLindner/plex-schedule-prerolls.git
```

### Install Requirements <a id="requirements"></a>

See `requirements.txt` for Python modules [link](requirements.txt)

Install Python requirements

```sh
pip install -r requirements.txt
```

### Create `config.ini` file with Plex connection information

Script supports:

- local ./config.ini (See: [Sample](sample_config.ini))
- PlexAPI global config.ini
- Custom location config.ini (see [Arguments](#arguments))

(See: [plexapi.CONFIG](https://python-plexapi.readthedocs.io/en/latest/configuration.html) for more info)

Feel free to rename `sample_config.ini` -> `config.ini` and update to your environment

Example `config.ini`

```ini
[auth]
server_baseurl = http://127.0.0.1:32400 # your plex server url
server_token = <PLEX_TOKEN> # access token
```

### Create `preroll_schedules.yaml` file with desired schedule

Feel free to rename `sample_preroll_schedules.yaml` -> `preroll_schedules.yaml` and update for your environment

Example YAML config layout (See: [Sample](sample_preroll_schedules.yaml) for more info)

```yaml
---
monthly:
    enabled: (yes/no)
    jan: /path/to/file.mp4;/path/to/file.mp4
    ...
    dec: jan: /path/to/file.mp4;/path/to/file.mp4
date_range:
    enabled: (yes/no)
    ranges:
    - start_date: 2020-01-01
      end_date: 2020-01-01
      path: /path/to/file(s)
    - start_date: 2020-07-04
      end_date: 2020-07-04
      path: /path/to/file(s)
weekly:
    enabled: (yes/no)
    1: /path/to/file(s)
    ...
    52: /path/to/file(s)
misc:
    enabled: (yes/no)
    always_use: /path/to/file(s)
default:
    enabled: (yes/no)
    path: /path/to/file.mp4;/path/to/file.mp4
```

### (Optional) Config `logger.conf` to your needs

See: [https://docs.python.org/3/howto/logging.html](https://docs.python.org/3/howto/logging.html)

---

## Usage <a id="usage"></a>

### Default Usage

```sh
python schedule_preroll.py
```

### Runtime Arguments <a id="arguments"></a>

- -v : version information
- -h : help information
- -c : config.ini (local or PlexAPI system central) for Connection Info (see [sample_config.ini](sample_config.ini))
- -s : preroll_schedules.yaml for various scheduling information (see [sample_preroll_schedules.yaml](sample_preroll_schedules.yaml))
- -l : location of custom logger.conf config file \
See:
  - Sample [logger config](logging.conf)
  - Logger usage [Examples](https://github.com/amilstead/python-logging-examples/blob/master/configuration/fileConfig/config.ini)
  - Logging [Info](https://www.internalpointers.com/post/logging-python-sub-modules-and-configuration-files)

```sh
python schedule_preroll.py -h

usage: schedule_preroll.py [-h] [-v] [-l LOG_CONFIG_FILE] [-c CONFIG_FILE] [-s SCHEDULE_FILE]

Automate scheduling of pre-roll intros for Plex

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show the version number and exit
  -l LOG_CONFIG_FILE, --logconfig-path LOG_CONFIG_FILE
                        Path to logging config file. [Default: ./logging.conf]
  -c CONFIG_FILE, --config-path CONFIG_FILE
                        Path to Config.ini to use for Plex Server info. [Default: ./config.ini]
  -s SCHEDULE_FILE, --schedule-path SCHEDULE_FILE
                        Path to pre-roll schedule file (YAML) to be use. [Default: ./preroll_schedules.yaml]
```

### Runtime Arguments Example

```sh
python schedule_preroll.py \
    -c path/to/custom/config.ini \
    -s path/to/custom/preroll_schedules.yaml \
    -l path/to/custom/logger.conf
```

---

## Scheduling (Optional)

Add to system scheduler:

Linux:

```sh
crontab -e
```

Place desired schedule (example below for everyday at midnight)

```sh
0 0 * * * python /path/to/schedule_preroll.py >/dev/null 2>&1
```

or \
(Optional) Wrap in a shell script: \
useful if running other scripts/commands, using venv encapsulation, customizing arguments

```sh
0 0 * * * /path/to/schedule_preroll.sh >/dev/null 2>&1
```

---

## Wrapping Up

> Sit back and enjoy the Intros!

---

## Shout out to places to get Pre-Roll

[https://prerolls.video](https://prerolls.video)