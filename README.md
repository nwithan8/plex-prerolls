# Plex Preroll Scheduler

A script to automate management of Plex pre-rolls.

Define when you want different pre-rolls to play throughout the year. For example:

- Holiday pre-roll rotations
- Special occasions
- Seasonal rotations
- Breaking up the monotony
- Keeping your family on their toes!

---

## Installation and Usage

### Run Script Directly

#### Requirements

- Python 3.8+

Clone the repo:

```sh
git clone https://github.com/nwithan8/plex-schedule-prerolls.git
```

Install Python requirements:

```sh
pip install -r requirements.txt
```

Copy `config.ini.sample` to `config.ini` and complete the `[auth]` section with your Plex server information.

Copy `schedules.yaml.sample` to `schedules.yaml` and [edit your schedule](#schedule-rules).

Run the script:

```sh
python schedule_preroll.py
```

#### Advanced Usage

```sh
$ python schedule_preroll.py -h

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
                        Path to pre-roll schedule file (YAML) to be use. [Default: ./schedules.yaml]
```

##### Example

```sh
python schedule_preroll.py \
    -c path/to/custom/config.ini \
    -s path/to/custom/schedules.yaml \
    -lc path/to/custom/logger.conf
```

### Run as Docker Container

#### Requirements

- Docker

#### Docker Compose

Complete the provided `docker-compose.yml` file and run:

```sh
docker-compose up -d
```

#### Docker CLI

```sh
docker run -d \
  --name=plex_prerolls \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e CRON_SCHEDULE="0 0 * * *" \
  -v /path/to/config:/config \
  -v /path/to/logs:/logs \
  --restart unless-stopped \
  nwithan8/plex_prerolls:latest
```

#### Paths and Environment Variables

| Path      | Description                                                                         |
|-----------|-------------------------------------------------------------------------------------|
| `/config` | Path to config files (`config.ini` and `schedule.yaml` should be in this directory) |
| `/logs`   | Path to log files (`schedule_preroll.log` will be in this directory)                |

| Environment Variable | Description                                                       |
|----------------------|-------------------------------------------------------------------|
| `PUID`               | UID of user to run as                                             |
| `PGID`               | GID of user to run as                                             |
| `TZ`                 | Timezone to use for cron schedule                                 |
| `CRON_SCHEDULE`      | Cron schedule to run script (see <https://crontab.guru> for help) |

---

## Schedule Rules

Schedules follow the following priority:
1. **misc**: Items listed in `always_use` will always be included (appended) to the preroll list

2. **date_range**: Schedule based on a specific date/time range

3. **weekly**: Schedule based on a specific week of the year

4. **monthly**: Schedule based on a specific month of the year

5. **default**: Default item to use if none of the above apply

For any conflicting schedules, the script tries to find the closest matching range and highest priority.

### Advanced Scheduling

#### Date Range Section Scheduling

`date_range` entries can accept both dates (`yyyy-mm-dd`) and datetimes (`yyyy-mm-dd hh:mm:ss`, 24-hour time).

`date_range` entries can also accept wildcards for any of the date/time fields. This can be useful for scheduling recurring events, such as annual events, "first-of-the-month" events, or even hourly events.

```yaml
date_range:
  enabled: true
  ranges:
    # Each entry requires start_date, end_date, path values
    - start_date: 2020-01-01 # Jan 1st, 2020
      end_date: 2020-01-02 # Jan 2nd, 2020
      path: /path/to/video.mp4
    - start_date: xxxx-07-04 # Every year on July 4th
      end_date: xxxx-07-04 # Every year on July 4th
      path: /path/to/video.mp4
    - start_date: xxxx-xx-02 # Every year on the 2nd of every month
      end_date: xxxx-xx-03 # Every year on the 3rd of every month
      path: /path/to/video.mp4
    - start_date: xxxx-xx-xx 08:00:00 # Every day at 8am
      end_date: xxxx-xx-xx 09:30:00 # Every day at 9:30am
      path: /path/to/holiday_video.mp4
```

You should [adjust your cron schedule](#scheduling-script) to run the script more frequently if you use this feature.

---

## Scheduling Script

**NOTE:** Scheduling is handled automatically in the Docker version of this script via the `CRON_SCHEDULE` environment variable.

### Linux

Add to system scheduler:

```sh
crontab -e
```

Place desired schedule (example below for every day at midnight)

```sh
0 0 * * * python /path/to/schedule_preroll.py >/dev/null 2>&1
```

You can also wrap the execution in a shell script (useful if running other scripts/commands, using venv encapsulation, customizing arguments, etc.)

```sh
0 0 * * * /path/to/schedule_preroll.sh >/dev/null 2>&1
```

Schedule as frequently as needed for your schedule (ex: hourly, daily, weekly, etc.)

---

## Shout out to places to get Pre-Roll

- <a href="https://prerolls.video" target="_blank"><https://prerolls.video></a>
