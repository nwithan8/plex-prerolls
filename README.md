# Schedule Plex server related Pre-roll intro videos

A helper script to automate management of Plex pre-rolls. \
Define when you want different pre-rolls to play throughout the year.

Ideas include:

- Holiday pre-roll rotations
- Special occasions
- Summer/Winter/Seasonal rotations
- Breaking up the monotony
- Keeping your family on their toes!

Simple steps:

> 1. Config the schedule
> 2. Schedule script on server
> 3. ...
> 4. Profit!

See [Installation & Setup](#install) section

---

## Schedule Rules

Schedule priority for a given Date:

1. **misc** \
always_use - always includes in listing (append)

2. **date_range** \
Include listing for the specified Start/End date range that include the given Date \
Range can be specified as a Date or DateTime \
Advanced features to have recurring timeframes \
**overrides usage of *week/month/default* listings

3. **weekly** \
Include listing for the specified WEEK of the year for the given Date \
  **override usage of *month/default* listings

4. **monthly** \
Include listing for the specified MONTH of the year for the given Date \
**overrides usage of *default* listings

5. **default** \
Default listing used of none of above apply to the given Date

Note: Script tries to find the closest matching range if multiple overlap at same time

---

## Installation & Setup <a id="install"></a>

Grab a copy of the code

```sh
cd /path/to/your/location
git clone https://github.com/BrianLindner/plex-schedule-prerolls.git
```

### Install Requirements <a id="requirements"></a>

Requires:

- Python 3.8+  [may work on 3.6+ but not tested]
- See `requirements.txt` for Python modules and versions [link](requirements.txt)
  - plexapi, configparser, pyyaml, etc.

Install Python requirements \
(highly recomend using <a href="https://docs.python.org/3/tutorial/venv.html" target="_blank">Virtual Environments</a> )

```sh
pip install -r requirements.txt
```

### Create `config.ini` file with Plex connection information

Script checks for:

- local ./config.ini (See: [Sample](config.ini.sample))
- PlexAPI global config.ini
- Custom location config.ini (see [Arguments](#arguments))

(See: <a href="https://python-plexapi.readthedocs.io/en/latest/configuration.html" target="_blank">plexapi.CONFIG</a> for more info)

Rename `config.ini.sample` -> `config.ini` and update to your environment

Example `config.ini`

```ini
[auth]
server_baseurl = http://127.0.0.1:32400 # your plex server url
server_token = <PLEX_TOKEN> # access token
```

### Create `preroll_schedules.yaml` file with desired schedule

#### Date Range Section Scheduling

Use it for *Day* or *Ranges of Dates* needs \
Now with Time support! (optional)

Formatting Supported:

- Dates: yyyy-mm-dd
- DateTime: yyyy-mm-dd hh:mm:ss  (24hr time format)

Rename `preroll_schedules.yaml.sample` -> `preroll_schedules.yaml` and update for your environment

Example YAML config layout (See: [Sample](preroll_schedules.yaml.sample) for more info)

```yaml
---
monthly:
  enabled: (yes/no)
  jan: /path/to/file.mp4;/path/to/file.mp4
  ...
  dec: /path/to/file.mp4;/path/to/file.mp4
date_range:
  enabled: (yes/no)
  ranges:
    - start_date: 2020-01-01
      end_date: 2020-01-01
      path: /path/to/video.mp4
    - start_date: 2020-07-03
      end_date: 2020-07-05
      path: /path/to/video.mp4
    - start_date: 2020-12-19
      end_date: 2020-12-26
      path: /path/to/video.mp4
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

See [Advancecd Date Ranges](#advanced_date) for additional features

## Usage <a id="usage"></a>

### Default Usage

```sh
python schedule_preroll.py
```

### Runtime Arguments <a id="arguments" ></a>

- -v : version information
- -h : help information
- -c : config.ini (local or PlexAPI system central) for Connection Info (see [config.ini.sample](config.ini.sample))
- -s : preroll_schedules.yaml for various scheduling information (see [spreroll_schedules.yaml.sample](preroll_schedules.yaml.sample))
- -lc : location of custom logger.conf config file \
See:
  - Sample [logger config](logging.conf)
  - Logger usage <a href="https://github.com/amilstead/python-logging-examples/blob/master/configuration/fileConfig/config.ini" target="_blank" >Examples</a>
  - Logging <a href="https://www.internalpointers.com/post/logging-python-sub-modules-and-configuration-files" target="_blank">Doc Info</a>

```sh
python schedule_preroll.py -h

usage: schedule_preroll.py [-h] [-v] [-l LOG_CONFIG_FILE] [-c CONFIG_FILE] [-s SCHEDULE_FILE]

Automate scheduling of pre-roll intros for Plex

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show the version number and exit
  -lc LOG_CONFIG_FILE, --logconfig-path LOG_CONFIG_FILE
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
    -lc path/to/custom/logger.conf
```

---

## Scheduling Script (Optional) <a id="scheduling"></a>

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

Schedule as frequently as needed for your environment and how specific and to your personal rotation schedule needs

---

## Advanced Date Range Section Scheduling <a id="advanced_date"></a> (Optional)

Date Ranges with Recurring Timeframes \
Useful for static dates or times where you want recurring preroll activity

Examples:

- Every Morning
- Yearly holidays (Halloween, New Years, Independence)
- Birthdays, Anniversaries

For either Start and/or End date of range \
Substitute "xx" for date/times to schedule for "any" \
Substitute "xxxx" for recurring year

- xxxx-xx-01 - Every first of month
- xxxx-xx-xx - Every day
- xxxx-xx-xx 08:00:00 - every day from 8am
- xxxx-01-01 - Every year on Jan 1 (new years day)
- xxxx-xx-01 xx:00:00 - 

if using Time, still must have a full datetime pattern (ex: hour, minute, second hh:mm:ss)

```yaml
#every July 4
- start_date: xxxx-07-04
  end_date: xxxx-07-04
  path: /path/to/video.mp4
# every first of month, all day
- start_date: xxxx-xx-01
  end_date: xxxx-xx-01
  path: /path/to/video.mp4
# 8-9 am every day
- start_date: xxxx-xx-xx 08:00:00
  end_date: xxxx-xx-xx 08:59:59
  path: /path/to/video.mp4

```

Note: Detailed time based schedules benefit from increased running of the Python script for frequently - ex: Hourly \
(See: [Scheduling Script](#scheduling) section)

---

## Config `logger.conf` to your needs (Optional)

See: <a href="https://docs.python.org/3/howto/logging.html" target="_blank"><https://docs.python.org/3/howto/logging.html></a>

---

## Wrapping Up

> Sit back and enjoy the Intros!

---

## Shout out to places to get Pre-Roll

- <a href="https://prerolls.video" target="_blank"><https://prerolls.video></a>
