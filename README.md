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

Copy `config.yaml.example` to `config.yaml`, provide your `plex` details and [edit your schedule](#schedule-rules).

Run the script:

```sh
python run.py
```

#### Advanced Usage

```sh
$ python run.py -h

usage: run.py [-h] [-c CONFIG] [-l LOG] [-d]

Plex Prerolls - A tool to manage prerolls for Plex

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to config file. Defaults to 'config.yaml'
  -l LOG, --log LOG     Log file directory. Defaults to 'logs/'
  -d, --dry-run         Dry run, no real changes made
```

##### Example

```sh
python run.py -c path/to/custom/config.yaml -l path/to/custom/log/directory/ # Trailing slash required
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
  -v /path/to/config:/ \
  -v /path/to/logs:/logs \
  --restart unless-stopped \
  nwithan8/plex_prerolls:latest
```

#### Paths and Environment Variables

| Path      | Description                                                           |
|-----------|-----------------------------------------------------------------------|
| `/config` | Path to config directory (`config.yaml` should be in this directory)  |
| `/logs`   | Path to log directory (`Plex Prerolls.log` will be in this directory) |

| Environment Variable | Description                                                       |
|----------------------|-------------------------------------------------------------------|
| `PUID`               | UID of user to run as                                             |
| `PGID`               | GID of user to run as                                             |
| `TZ`                 | Timezone to use for cron schedule                                 |
| `CRON_SCHEDULE`      | Cron schedule to run script (see <https://crontab.guru> for help) |

---

## Schedule Rules

Any entry whose schedule falls within the current date/time at the time of execution will be added to the preroll.

You can define as many schedules as you want, in the following categories (order does not matter):

1. **always**: Items listed here will always be included (appended) to the preroll list
    - If you have a large set of prerolls, you can provide all paths and use `random_count` to randomly select a smaller
      subset of the list to use on each run.

2. **date_range**: Schedule based on a specific date/time range (including [wildcards](#date-range-section-scheduling))

3. **weekly**: Schedule based on a specific week of the year

4. **monthly**: Schedule based on a specific month of the year

### Advanced Scheduling

#### Date Range Section Scheduling

`date_range` entries can accept both dates (`yyyy-mm-dd`) and datetimes (`yyyy-mm-dd hh:mm:ss`, 24-hour time).

`date_range` entries can also accept wildcards for any of the date/time fields. This can be useful for scheduling
recurring events, such as annual events, "first-of-the-month" events, or even hourly events.

```yaml
date_range:
  enabled: true
  ranges:
    # Each entry requires start_date, end_date, path values
    - start_date: 2020-01-01 # Jan 1st, 2020
      end_date: 2020-01-02 # Jan 2nd, 2020
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
      weight: 2 # Add these paths to the list twice (make up greater percentage of prerolls - more likely to be selected)
    - start_date: xxxx-07-04 # Every year on July 4th
      end_date: xxxx-07-04 # Every year on July 4th
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
      weight: 1
    - name: "My Schedule" # Optional name for logging purposes
      start_date: xxxx-xx-02 # Every year on the 2nd of every month
      end_date: xxxx-xx-03 # Every year on the 3rd of every month
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
      weight: 1
    - start_date: xxxx-xx-xx 08:00:00 # Every day at 8am
      end_date: xxxx-xx-xx 09:30:00 # Every day at 9:30am
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
      weight: 1
```

You should [adjust your cron schedule](#scheduling-script) to run the script more frequently if you use this feature.

`date_range` entries also accept an optional `weight` value that can be used to adjust the emphasis of this entry over
others by adding the listed paths multiple times. Since Plex selects a random preroll from the list of paths, having the
same path listed multiple times increases its chances of being selected over paths that only appear once. This allows
you to combine, e.g. a `date_range` entry with a `misc` entry, but place more weight/emphasis on the `date_range` entry.

`date_range` entries also accept an optional `name` value that can be used to identify the schedule in the logs.

---

## Scheduling Script

**NOTE:** Scheduling is handled automatically in the Docker version of this script via the `CRON_SCHEDULE` environment
variable.

### Linux

Add to system scheduler:

```sh
crontab -e
```

Place desired schedule (example below for every day at midnight)

```sh
0 0 * * * python /path/to/run.py >/dev/null 2>&1
```

You can also wrap the execution in a shell script (useful if running other scripts/commands, using venv encapsulation,
customizing arguments, etc.)

```sh
0 0 * * * /path/to/run_prerolls.sh >/dev/null 2>&1
```

Schedule as frequently as needed for your schedule (ex: hourly, daily, weekly, etc.)

---

## Shout out to places to get Pre-Roll

- <a href="https://prerolls.video" target="_blank"><https://prerolls.video></a>
