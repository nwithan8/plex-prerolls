<div align="center">
<img src="https://raw.githubusercontent.com/nwithan8/plex-prerolls/main/documentation/images/logo.png" alt="logo" width="300">
<h1>Plex Prerolls</h1>
<p>A script to automate management of Plex pre-rolls.</p>
</div>

---

## Installation and Usage

### Run Script Directly

With the introduction of webhook ingestion and auto-generation of prerolls, it is no longer advised to run this
application as a direct Python script. Please use the [Docker container](#run-as-docker-container) instead.

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
  -p 8283:8283 \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e CRON_SCHEDULE="0 0 * * *" \
  -e DRY_RUN=false \
  -v /path/to/config:/ \
  -v /path/to/logs:/logs \
  -v /path/to/preroll/files:/files \
  -v /path/to/auto-generated/rolls/temp:/renders \
  -v /path/to/auto-generated/rolls/parent:/auto_rolls \
  --restart unless-stopped \
  nwithan8/plex_prerolls:latest
```

#### Paths and Environment Variables

| Path          | Description                                                                                                                  |
|---------------|------------------------------------------------------------------------------------------------------------------------------|
| `/config`     | Path to config directory (`config.yaml` should be in this directory)                                                         |
| `/logs`       | Path to log directory (`Plex Prerolls.log` will be in this directory)                                                        |
| `/files`      | Path to the root directory of all preroll files (for [Path Globbing](#path-globbing) feature)                                |
| `/auto_rolls` | Path to the root directory where all [auto-generated prerolls files](#auto-generation) will be stored                        |
| `/renders`    | Path to where [auto-generated prerolls](#auto-generation) and associated assets will be temporarily stored during generation |

| Environment Variable | Description                                                       |
|----------------------|-------------------------------------------------------------------|
| `PUID`               | UID of user to run as                                             |
| `PGID`               | GID of user to run as                                             |
| `TZ`                 | Timezone to use for cron schedule                                 |
| `CRON_SCHEDULE`      | Cron schedule to run script (see <https://crontab.guru> for help) |
| `DRY_RUN`            | Don't actually make changes to Plex prerolls, only simulate       |

---

## Schedule Rules

Any entry whose schedule falls within the current date/time at the time of execution will be added to the preroll.

You can define as many schedules as you want, in the following categories (order does not matter):

1. **always**: Items listed here will always be included (appended) to the preroll list
    - If you have a large set of prerolls, you can provide all paths and use `count` to randomly select a smaller
      subset of the list to use on each run.

2. **date_range**: Schedule based on a specific date/time range (including [wildcards](#date-range-section-scheduling))

3. **weekly**: Schedule based on a specific week of the year

4. **monthly**: Schedule based on a specific month of the year

### Advanced Scheduling

#### Weight

All schedule entries accept an optional `weight` value that can be used to adjust the emphasis of this entry over
others by adding the listed paths multiple times. Since Plex selects a random preroll from the list of paths, having the
same path listed multiple times increases its chances of being selected over paths that only appear once. This allows
you to combine, e.g. a `date_range` entry with an `always` entry, but place more weight/emphasis on the `date_range`
entry.

```yaml
date_range:
  enabled: true
  ranges:
    - start_date: 2020-01-01 # Jan 1st, 2020
      end_date: 2020-01-02 # Jan 2nd, 2020
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
      weight: 2 # Add these paths to the list twice (make up greater percentage of prerolls - more likely to be selected)
```

#### Disable Always

Any schedule entry (except for the `always` section) can disable the inclusion of the `always` section by setting the
`disable_always` value to `true`. This can be useful if you want to make one specific, i.e. `date_range` entry for a
holiday,
and you don't want to include the `always` section for this specific holiday, but you still want to include the `always`
section
for other holidays.

```yaml
date_range:
  enabled: true
  ranges:
    - start_date: 2020-01-01 # Jan 1st, 2020
      end_date: 2020-01-02 # Jan 2nd, 2020
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
      disable_always: true # Disable the inclusion of the `always` section when this entry is active
```

#### Path Globbing

**NOTE**: This feature will only work if you are running the Docker container on the same machine as your Plex
server.

Instead of listing out each individual preroll file, you can use glob (wildcard) patterns to match multiple files in a
specific directory.

The application will search for all files on your local filesystem that match the pattern(s) and automatically translate
them to Plex-compatible remote paths.

##### Setup

Enable the feature under the `path_globbing` section of each schedule.

Each `pair` is a local (`root_path`) path and remote (`plex_path`) path that correspond to each other.
The `patterns` list is a list of glob patterns that will be searched for in the `root_path` directory and translated to
the `plex_path`-directory equivalent.

You can provide multiple `pairs` to match multiple local-remote directory pairs and multiple subsequent glob patterns.

```yaml
  path_globbing:
    enabled: true
    pairs:
      - root_path: /files # The root folder to use for globbing
        plex_path: /path/to/prerolls/in/plex # The path to use for the Plex server
        patterns:
          - "local/path/to/prerolls/*.mp4" # The pattern to look for in the root_path
          - "local/path/to/prerolls/*.mkv" # The pattern to look for in the root_path
      - root_path: /other/files
        plex_path: /path/to/other/prerolls/in/plex
        patterns:
          - "local/path/to/prerolls/*.mp4"
          - "local/path/to/prerolls/*.mkv"
```

For example, if your prerolls on your file system are located at `/mnt/user/media/prerolls` and Plex sees them at
`/media/prerolls`, you would set the `root_path` to `/mnt/user/media/prerolls` and the `plex_path` to `/media/prerolls`.

If you are using the Docker container, you can mount the preroll directory to the container at any location you would
prefer (recommended: `/files`) and set the `root_path` accordingly. Although you can define multiple roots, it is
recommended to use a single all-encompassing root folder and rely on more-detailed glob patterns to match files in
specific subdirectories.

If you are using the Unraid version of this container, the "Files Path" path is mapped to `/files` by default; you
should set `root_path` to `/files` and `plex_path` to the same directory as seen by Plex.

#### Usage

In any schedule section, you can use the `path_globbing` key to specify glob pattern rules to match files.

```yaml
always:
  enabled: true
  paths:
    - /remote/path/1.mp4
    - /remote/path/2.mp4
    - /remote/path/3.mp4
  path_globbing:
    enabled: true
    pairs:
      - root_path: /files
        plex_path: /path/to/prerolls/in/plex
        patterns:
          - "*.mp4"
```

The above example will match all `.mp4` files in the `root_path` directory and append them to the list of prerolls.

If you have organized your prerolls into subdirectories, you can specify specific subdirectories to match, or use `**`
to match all subdirectories.

```yaml
always:
  enabled: true
  paths:
    - /remote/path/1.mp4
    - /remote/path/2.mp4
    - /remote/path/3.mp4
  path_globbing:
    enabled: true
    pairs:
      - root_path: /files
        plex_path: /path/to/prerolls/in/plex
        patterns:
          - "subdir1/*.mp4"
          - "subdir2/*.mp4"
          - "subdir3/**/*.mp4"
```

You can use both `paths` and `path_globbing` in the same section, allowing you to mix and match specific files with glob
patterns. Please note that `paths` entries must be fully-qualified **remote** paths (as seen by Plex), while `pattern`
entries in `path_globbing` are relative to the **local** `root_path` directory.

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
    - start_date: xxxx-07-04 # Every year on July 4th
      end_date: xxxx-07-04 # Every year on July 4th
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
    - name: "My Schedule" # Optional name for logging purposes
      start_date: xxxx-xx-02 # Every year on the 2nd of every month
      end_date: xxxx-xx-03 # Every year on the 3rd of every month
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
    - start_date: xxxx-xx-xx 08:00:00 # Every day at 8am
      end_date: xxxx-xx-xx 09:30:00 # Every day at 9:30am
      paths:
        - /path/to/video.mp4
        - /path/to/another/video.mp4
```

You should [adjust your cron schedule](#scheduling-script) to run the script more frequently if you use this feature.

`date_range` entries also accept an optional `name` value that can be used to identify the schedule in the logs.

---

## Advanced Configuration

### Auto-Generation

**NOTE**: This feature will only work if you are running the Docker container on the same machine as your Plex
server.

**NOTE**: This feature relies on Plex webhooks, which require a Plex Pass subscription.

Plex Prerolls can automatically generate prerolls, store the generated files in a specified directory and include them
in the list of prerolls.

#### "Recently Added Media" Pre-Rolls

The application can generate trailer-like prerolls for each new media item added to your library (with a rolling total,
defaults to 10 items).

This is done by receiving a webhook from Plex when new media is added, retrieving a trailer and soundtrack (via YouTube)
as well as poster and metadata for the media item, and generating a preroll from these assets.

Example of a generated preroll:

<img src="https://raw.githubusercontent.com/nwithan8/plex-prerolls/main/documentation/images/recently-added-preroll-example.png" alt="logo" width="300">

> :warning: This feature requires [extracting cookies for YouTube](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp) and storing them in a file called `yt_dlp_cookies.txt` alongside your `config.yaml` file.

##### Setup

[Set up a Plex webhook](https://support.plex.tv/articles/115002267687-webhooks/) to point to the application's
`/recently-added` endpoint (e.g. `http://localhost:8283/recently-added`).

Because this feature requires Plex Prerolls and Plex Media Server to be running on the same host machine, it is highly
recommended to use internal networking (local IP addresses) rather than publicly exposing Plex Prerolls to the Internet.

---

## Shout out to places to get Pre-Roll

- <a href="https://prerolls.video" target="_blank"><https://prerolls.video></a>

---

## FAQ

**Can this work with Jellyfin?**

Jellyfin has an [Intros plugin](https://github.com/jellyfin/jellyfin-plugin-intros) that already replicates this
functionality, in terms of setting rules (including based on schedule, as well as based on the about-to-play media item)
for prerolls. I recommend using that plugin instead.

**Can this work with Emby?**

Emby has a [Cinema Intros plugin](https://emby.media/support/articles/Cinema-Intros.html) with a
similar ["list of videos" option](https://emby.media/support/articles/Cinema-Intros.html#custom-intros). Currently,
there is **no way** to update this setting via Emby's API, so there is no way to automate this process. I am in
communication with the Emby development team to see if this feature can be added.


## Credit

- [BrianLindner](https://github.com/BrianLindner) for the [original pre-roll scheduling concept](https://github.com/BrianLindner/plex-schedule-prerolls)
- [AndrewHolmes060](https://github.com/AndrewHolmes060) for the [original trailer auto-generation feature](https://github.com/AndrewHolmes060/Plex-Preroll-Builder)