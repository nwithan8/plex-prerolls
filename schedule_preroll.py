#!/usr/bin/python
"""Schedule Plex server related Pre-roll Intro videos
A helper script to automate management of Plex pre-rolls.
Define when you want different pre-rolls to play throughout the year.

Set it and forget it!

Optional Arguments:
  -h, --help            show this help message and exit
  -v, --version         show the version number and exit
  -lc LOG_CONFIG_FILE, --logconfig-path LOG_CONFIG_FILE
                        Path to logging config file.
                        [Default: ./logging.conf]
  -c CONFIG_FILE, --config-path CONFIG_FILE
                        Path to Config.ini to use for Plex Server info.
                        [Default: ./config.ini]
  -s SCHEDULE_FILE, --schedule-path SCHEDULE_FILE
                        Path to pre-roll schedule file (YAML) to be used.
                        [Default: ./schedules.yaml]

Requirements:
- See Requirements.txt for Python modules

Scheduling:
    Add to system scheduler such as:
    > crontab -e
    > 0 0 * * * python path/to/schedule_pre_roll.py >/dev/null 2>&1

Raises:
    FileNotFoundError: [description]
    KeyError: [description]
    ConfigError: [description]
    FileNotFoundError: [description]
"""
import enum
import json
import logging
import os
import random
import sys
from argparse import ArgumentParser, Namespace
from datetime import date, datetime, timedelta
from typing import List, NamedTuple, Optional, Tuple, Union

import requests
import urllib3  # type: ignore
import yaml
from cerberus import Validator  # type: ignore
from cerberus.schema import SchemaError
from plexapi.server import PlexServer

from util import plexutil

logger = logging.getLogger(__name__)

script_filename = os.path.basename(sys.argv[0])
script_name = os.path.splitext(script_filename)[0]
script_dir = os.path.dirname(__file__)


class ScheduleEntry(NamedTuple):
    type: str
    start_date: datetime
    end_date: datetime
    path: str
    weight: int


class ScheduleType(enum.Enum):
    default = "default"
    monthly = "monthly"
    weekly = "weekly"
    date_range = "date_range"
    misc = "misc"


def schedule_types() -> list[str]:
    """Return a list of Schedule Types

    Returns:
        List[ScheduleType]: List of Schedule Types
    """
    return [_enum.value for _enum in ScheduleType]


def arguments() -> Namespace:
    """Setup and Return command line arguments
    See https://docs.python.org/3/howto/argparse.html

    Returns:
        argparse.Namespace: Namespace object
    """
    description = "Automate scheduling of pre-roll intros for Plex"
    version = "0.12.4"

    config_default = "./config.ini"
    log_config_default = "./logging.conf"
    schedule_default = "./schedules.yaml"
    parser = ArgumentParser(description=f"{description}")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {version}",
        help="show the version number and exit",
    )
    parser.add_argument(
        "-lc",
        "--logconfig-file",
        dest="log_config_file",
        action="store",
        default=log_config_default,
        help=f"Path to logging config file. [Default: {log_config_default}]",
    )
    parser.add_argument(
        "-t",
        "--test-run",
        dest="do_test_run",
        action="store_true",
        default=False,
        help="Perform a test run, display output but dont save",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        dest="config_file",
        action="store",
        help=f"Path to Config.ini to use for Plex Server info. [Default: {config_default}]",
    )
    parser.add_argument(
        "-s",
        "--schedule-file",
        dest="schedule_file",
        action="store",
        help=f"Path to pre-roll schedule file (YAML) to be use. [Default: {schedule_default}]",
    )
    args = parser.parse_args()

    return args


def week_range(year: int, week_num: int) -> Tuple[datetime, datetime]:
    """Return the starting/ending date range of a given year/week

    Args:
        year (int):     Year to calc range for
        week_num (int):  Month of the year (1-12)

    Returns:
        DateTime: Start date of the Year/Month
        DateTime: End date of the Year/Month
    """
    start = datetime.strptime(f"{year}-W{int(week_num) - 1}-0", "%Y-W%W-%w").date()
    end = start + timedelta(days=6)

    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.max.time())

    return start, end


def month_range(year: int, month_num: int) -> Tuple[datetime, datetime]:
    """Return the starting/ending date range of a given year/month

    Args:
        year (int):     Year to calc range for
        month_num (int): Month of the year (1-12)

    Returns:
        DateTime: Start date of the Year/Month
        DateTime: End date of the Year/Month
    """
    start = date(year, month_num, 1)
    next_month = start.replace(day=28) + timedelta(days=4)
    end = next_month - timedelta(days=next_month.day)

    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.max.time())

    return start, end


def duration_seconds(start: Union[date, datetime], end: Union[date, datetime]) -> float:
    """Return length of time between two date/datetime in seconds

    Args:
        start (date/datetime): [description]
        end (date/datetime): [description]

    Returns:
        float: Length in time seconds
    """
    if not isinstance(start, datetime):
        start = datetime.combine(start, datetime.min.time())
    if not isinstance(end, datetime):
        end = datetime.combine(end, datetime.max.time())

    delta = end - start

    logger.debug(
        "duration_second[] Start: %s End: %s Duration: %s}", start, end, delta.total_seconds()
    )
    return delta.total_seconds()


def make_datetime(value: Union[str, date, datetime], lowtime: bool = True) -> datetime:
    """Returns a DateTime object with a calculated Time component if none provided
      converts:
      * Date to DateTime, with a Time of Midnight 00:00 or 11:59 pm
      * String to DateTime, with a Time as defined in the string

    Args:
        value (Union[str, date, datetime]): Input value to convert to a DateTime object
        lowtime (bool, optional): Calculate time to be midnight (True) or 11:59 PM (False).
                                    Defaults to True.

    Raises:
        TypeError: Unknown type to calculate

    Returns:
        datetime: DateTime object with time component set if none provided
    """
    today = date.today()
    now = datetime.now()
    dt_val = datetime(today.year, today.month, today.day, 0, 0, 0)

    # append the low or high time of the day
    if lowtime:
        time = datetime.min.time()
    else:
        time = datetime.max.time()

    # determine how to translate the input value
    if isinstance(value, datetime):  # type: ignore
        dt_val = value
    elif isinstance(value, date):  # type: ignore
        dt_val = datetime.combine(value, time)
    elif isinstance(value, str):  # type: ignore
        try:
            # Expect format of DateType string to be (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
            # allow 'xx' to denote 'every' similar to Cron "*"
            logger.debug('Translating string value="%s" to datetime (LowTime=%s)', value, lowtime)

            # default to today and the time period (low/high)
            year, month, day = today.year, today.month, today.day
            hour, minute, second = time.hour, time.minute, time.second

            # start parsing the timeout, for later additional processing
            date_parts = value.lower().split("-")

            year = today.year if date_parts[0] == "xxxx" else int(date_parts[0])
            month = today.month if date_parts[1] == "xx" else int(date_parts[1])

            date_parts_day = date_parts[2].split(" ")

            day = today.day if date_parts_day[0] == "xx" else int(date_parts_day[0])

            # attempt to parse out Time components
            if len(date_parts_day) > 1:
                time_parts = date_parts_day[1].split(":")
                if len(time_parts) > 1:
                    hour = now.hour if time_parts[0] == "xx" else int(time_parts[0])
                    minute = now.minute if time_parts[1] == "xx" else int(time_parts[1])
                    second = now.second + 1 if time_parts[2] == "xx" else int(time_parts[2])

            dt_val = datetime(year, month, day, hour, minute, second)
            logger.debug("Datetime-> '%s'", dt_val)
        except Exception as e:
            logger.error('Unable to parse date string "%s"', value, exc_info=e)
            raise
    else:
        msg = 'UnknownType: Unable to parse date string "%s" for type "%s"'
        logger.error(msg, value, type(value))
        raise TypeError(msg)

    return dt_val


def schedule_file_contents(schedule_filename: Optional[str]) -> dict[str, any]:  # type: ignore
    """Returns a contents of the provided YAML file and validates

    Args:
        schedule_filename (string, optional]): schedule file to load, will use defaults if not specified

    Raises:
        Validation Errors

    Returns:
        YAML Contents: YAML structure of Dict[str, Any]
    """
    default_files = ["schedules.yaml"]

    filename = None
    if schedule_filename not in ("", None):
        if os.path.exists(str(schedule_filename)):
            filename = schedule_filename

            logger.debug('using specified schedule file "%s"', filename)
        else:
            msg = f'Pre-roll Schedule file "{schedule_filename}" not found'
            logger.error(msg)
            raise FileNotFoundError(msg)
    else:
        for f in default_files:
            default_file = os.path.join(script_dir, f)
            if os.path.exists(default_file):
                filename = default_file
                logger.debug('using default schedule file "%s"', filename)
                break

    # if we still cant find a schedule file, we abort
    if not filename:
        file_str = '" / "'.join(default_files)
        logger.error('Missing schedule file: "%s"', file_str)
        raise FileNotFoundError(file_str)

    schema_filename = os.path.join(script_dir, "util/schedule_file_schema.json")

    logger.debug('using schema validation file "%s"', schema_filename)

    # make sure the Schema validation file is available
    if not os.path.exists(str(schema_filename)):
        msg = f'Pre-roll Schema Validation file "{schema_filename}" not found'
        logger.error(msg)
        raise FileNotFoundError(msg)

    # Open Schedule file
    try:
        with open(filename, "r", encoding="utf8") as file:
            contents = yaml.load(file, Loader=yaml.SafeLoader)  # type: ignore
    except yaml.YAMLError as ye:
        logger.error("YAML Error: %s", filename, exc_info=ye)
        raise
    except Exception as e:
        logger.error(e, exc_info=e)
        raise

    # Validate the loaded YAML data against the required schema
    try:
        with open(schema_filename, "r", encoding="utf8") as schema_file:
            schema = json.loads(schema_file.read())

        v = Validator(schema)  # type: ignore
    except json.JSONDecodeError as je:
        logger.error("JSON Error: %s", schema_filename, exc_info=je)
        raise
    except SchemaError as se:
        logger.error("Schema Error %s", schema_filename, exc_info=se)
        raise
    except Exception as e:
        logger.error(e, exc_info=e)
        raise

    if not v.validate(contents):  # type: ignore
        logger.error("Pre-roll Schedule YAML Validation Error: %s", v.errors)  # type: ignore
        raise yaml.YAMLError(f"Pre-roll Schedule YAML Validation Error: {v.errors}")  # type: ignore

    return contents


def prep_weekly_schedule(contents: dict[str, any]) -> List[ScheduleEntry]:
    """
    Collect all weekly ScheduleEntries that are valid for the current datetime
    """
    schedule_entries: List[ScheduleEntry] = []

    if not contents.get("enabled", False):
        return schedule_entries

    today = date.today()
    for i in range(1, 53):
        try:
            path = str(contents[i])  # type: ignore

            if path:
                start, end = week_range(today.year, i)

                entry = ScheduleEntry(
                    type=ScheduleType.weekly.value,
                    start_date=start,
                    end_date=end,
                    path=path,
                    weight=contents.get("weight", 1),
                )

                schedule_entries.append(entry)
        except KeyError:
            # skip KeyError for missing Weeks
            pass

    return schedule_entries


def prep_monthly_schedule(contents: dict[str, any]) -> List[ScheduleEntry]:
    """
    Collect all monthly ScheduleEntries that are valid for the current datetime
    """
    schedule_entries: List[ScheduleEntry] = []

    if not contents.get("enabled", False):
        return schedule_entries

    # Get the entry for the current month
    today = date.today()
    today_month_abbrev = date(today.year, today.month, 1).strftime("%b").lower()
    path = contents.get(today_month_abbrev, None)
    if not path:
        return schedule_entries

    start, end = month_range(today.year, today.month)

    logger.debug(f'Parsing paths for current month: {today_month_abbrev}')

    entry = ScheduleEntry(
        type=ScheduleType.monthly.value,
        start_date=start,
        end_date=end,
        path=path,
        weight=contents.get("weight", 1),
    )

    schedule_entries.append(entry)

    return schedule_entries


def prep_date_range_schedule(contents: dict[str, any]) -> List[ScheduleEntry]:
    """
    Collect all date_range ScheduleEntries that are valid for the current datetime
    """
    schedule_entries: List[ScheduleEntry] = []

    if not contents.get("enabled", False):
        return schedule_entries

    for _range in contents.get('ranges', []):
        path = _range.get("path", None)
        if not path:
            logger.error(f'Missing "path" entry in date_range: {_range}')
            continue

        start = make_datetime(_range["start_date"], lowtime=True)  # type: ignore
        end = make_datetime(_range["end_date"], lowtime=False)  # type: ignore

        # Skip if the current date is not within the range
        now = datetime.now()
        if start > now or end < now:
            logger.debug(f'Skipping date_range out of range: {_range}')
            continue

        entry = ScheduleEntry(
            type=ScheduleType.date_range.value,
            start_date=start,
            end_date=end,
            path=path,
            weight=_range.get("weight", 1),
        )

        schedule_entries.append(entry)

    return schedule_entries


def prep_misc_schedule(contents: dict[str, any]) -> List[ScheduleEntry]:
    """
    Collect all misc ScheduleEntries
    """
    schedule_entries: List[ScheduleEntry] = []

    if not contents.get("enabled", False):
        return schedule_entries

    today = date.today()
    path = contents.get("always_use", None)
    if not path:
        return schedule_entries

    logger.debug(f'Parsing "misc" selections: {path}')

    random_count = contents.get("random_count", -1)
    if random_count > -1:
        path_items = path.split(";")
        path_items = random.sample(population=path_items, k=random_count)
        path = ";".join(path_items)

    entry = ScheduleEntry(
        type=ScheduleType.misc.value,
        start_date=datetime(today.year, today.month, today.day, 0, 0, 0),
        end_date=datetime(today.year, today.month, today.day, 23, 59, 59),
        path=path,
        weight=contents.get("weight", 1),
    )
    schedule_entries.append(entry)

    return schedule_entries


def prep_default_schedule(contents: dict[str, any]) -> List[ScheduleEntry]:
    """
    Collect all default ScheduleEntries
    """
    schedule_entries: List[ScheduleEntry] = []

    if not contents.get("enabled", False):
        return schedule_entries

    today = date.today()
    path = contents.get("path", None)
    if not path:
        return schedule_entries

    logger.debug(f'Parsing "default" selections: {path}')

    entry = ScheduleEntry(
        type=ScheduleType.default.value,
        start_date=datetime(today.year, today.month, today.day, 0, 0, 0),
        end_date=datetime(today.year, today.month, today.day, 23, 59, 59),
        path=path,
        weight=contents.get("weight", 1),
    )
    schedule_entries.append(entry)

    return schedule_entries


def pre_roll_schedule(schedule_file: Optional[str] = None) -> List[ScheduleEntry]:
    """Return a listing of defined pre_roll schedules for searching/use

    Args:
        schedule_file (str): path/to/schedule_pre_roll.yaml style config file (YAML Format)

    Raises:
        FileNotFoundError: If no schedule config file exists

    Returns:
        list: list of ScheduleEntries
    """

    contents = schedule_file_contents(schedule_file)  # type: ignore

    schedule_entries: List[ScheduleEntry] = []

    for schedule_type in schedule_types():

        section_contents = contents.get(schedule_type, None)
        if not section_contents:
            logger.info('"%s" section not included in schedule file; skipping', schedule_type)
            # continue to other sections
            continue

        # Write a switch statement to handle each schedule type
        match schedule_type:
            case ScheduleType.weekly.value:
                weekly_schedule_entries = prep_weekly_schedule(section_contents)
                schedule_entries.extend(weekly_schedule_entries)

            case ScheduleType.monthly.value:
                monthly_schedule_entries = prep_monthly_schedule(section_contents)
                schedule_entries.extend(monthly_schedule_entries)

            case ScheduleType.date_range.value:
                date_range_schedule_entries = prep_date_range_schedule(section_contents)
                schedule_entries.extend(date_range_schedule_entries)

            case ScheduleType.misc.value:
                misc_schedule_entries = prep_misc_schedule(section_contents)
                schedule_entries.extend(misc_schedule_entries)

            case ScheduleType.default.value:
                default_schedule_entries = prep_default_schedule(section_contents)
                schedule_entries.extend(default_schedule_entries)

            case _:
                logger.error('Unknown schedule_type "%s" detected', schedule_type)

    # Sort list so most recent Ranges appear first
    schedule_entries.sort(reverse=True, key=lambda x: x.start_date)

    logger.debug("***START Schedule Set to be used***")
    logger.debug(schedule_entries)
    logger.debug("***END Schedule Set to be used***")

    return schedule_entries


def build_listing_string(items: List[str], play_all: bool = False) -> str:
    """Build the Plex formatted string of pre_roll paths

    Args:
        items (list):               List of pre_roll video paths to place into a string listing
        play_all (bool, optional):  Play all videos. [Default: False (Random choice)]

    Returns:
        string: CSV Listing (, or ;) based on play_all param of pre_roll video paths
    """

    if not items:
        return ""

    if play_all:
        # use , to play all entries
        return ",".join(items)

    return ";".join(items)


def pre_roll_listing(schedule_entries: List[ScheduleEntry], for_datetime: Optional[datetime] = None) -> str:
    """Return listing of pre_roll videos to be used by Plex

    Args:
        schedule_entries (List[ScheduleEntry]):     List of schedule entries (See: getPrerollSchedule)
        for_datetime (datetime, optional):  Date to process pre-roll string for [Default: Today]
                                            Useful for simulating what different dates produce

    Returns:
        string: listing of pre_roll video paths to be used for Extras. CSV style: (;|,)
    """
    entries: list[str] = []
    default_entry_needed = True

    _schedule_types = schedule_types()

    # determine which date to build the listing for
    if for_datetime:
        if isinstance(for_datetime, datetime):  # type: ignore
            check_datetime = for_datetime
        else:
            check_datetime = datetime.combine(for_datetime, datetime.now().time())
    else:
        check_datetime = datetime.now()

    # process the schedule for the given date
    for entry in schedule_entries:
        entry_start = entry.start_date
        if not isinstance(entry_start, datetime):  # type: ignore
            entry_start = datetime.combine(entry_start, datetime.min.time())

        entry_end = entry.end_date
        if not isinstance(entry_end, datetime):  # type: ignore
            entry_end = datetime.combine(entry_end, datetime.max.time())

        logger.debug(
            'checking "%s" against: "%s" - "%s"', check_datetime, entry_start, entry_end
        )

        # If current schedule entry is not valid for the current date, skip it
        # This shouldn't be needed, as ScheduleEntries are only added up to this point if valid for the current datetime
        if entry_start > check_datetime or entry_end < check_datetime:
            continue

        if entry.type != ScheduleType.default.value:  # Non-default entry, so don't need to add default entry
            default_entry_needed = False
            for _ in range(entry.weight):  # Add entry to list multiple times based on weight
                entries.append(entry.path)
        else:  # Default entry, only add if no other entries have been added
            if default_entry_needed:
                entries.append(entry.path)  # Default will only be added once (no weight)

    listing = build_listing_string(items=entries)

    return listing


def save_pre_roll_listing(plex: PlexServer, pre_roll_listing: Union[str, List[str]]) -> None:
    """Save Plex Preroll info to PlexServer settings

    Args:
        plex (PlexServer): Plex server to update
        pre_roll_listing (str, list[str]): csv listing or List of pre_roll paths to save
    """
    # if happened to send in an Iterable List, merge to a string
    if isinstance(pre_roll_listing, list):
        pre_roll_listing = build_listing_string(list(pre_roll_listing))

    logger.debug('Attempting save of pre-rolls: "%s"', pre_roll_listing)

    plex.settings.get("cinemaTrailersPrerollID").set(pre_roll_listing)  # type: ignore
    try:
        plex.settings.save()  # type: ignore
    except Exception as e:
        logger.error('Unable to save Pre-Rolls to Server: "%s"', plex.friendlyName, exc_info=e)  # type: ignore
        raise e

    logger.info('Saved Pre-Rolls: Server: "%s" Pre-Rolls: "%s"', plex.friendlyName, pre_roll_listing)  # type: ignore


if __name__ == "__main__":
    args = arguments()

    plexutil.init_logger(args.log_config_file)

    cfg = plexutil.plex_config(args.config_file)

    # Initialize Session information
    sess = requests.Session()
    # Ignore verifying the SSL certificate
    sess.verify = False  # '/path/to/certfile'
    # If verify is set to a path of a directory (not a cert file),
    # the directory needs to be processed with the c_rehash utility
    # from OpenSSL.
    if sess.verify is False:
        # Disable the warning that the request is insecure, we know that...
        # import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # type: ignore

    try:
        plex = PlexServer(cfg["PLEX_URL"], cfg["PLEX_TOKEN"], session=sess)
    except Exception as e:
        logger.error("Error connecting to Plex", exc_info=e)
        raise e

    schedule_entries = pre_roll_schedule(args.schedule_file)
    pre_rolls = pre_roll_listing(schedule_entries=schedule_entries)

    if args.do_test_run:
        msg = f"Test Run of Plex Pre-Rolls: **Nothing being saved**\n{pre_rolls}\n"
        logger.debug(msg)
        print(msg)
    else:
        save_pre_roll_listing(plex, pre_rolls)
