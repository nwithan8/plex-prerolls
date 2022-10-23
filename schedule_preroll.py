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
                        Path to pre-roll schedule file (YAML) to be use.
                        [Default: ./preroll_schedules.yaml]

Requirements:
- See Requirements.txt for Python modules

Scheduling:
    Add to system scheduler such as:
    > crontab -e
    > 0 0 * * * python path/to/schedule_preroll.py >/dev/null 2>&1

Raises:
    FileNotFoundError: [description]
    KeyError: [description]
    ConfigError: [description]
    FileNotFoundError: [description]
"""


import json
import logging
import os
import sys
from argparse import ArgumentParser, Namespace
from datetime import date, datetime, timedelta
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

import requests
import urllib3
import yaml
from cerberus import Validator  # type: ignore
from cerberus.schema import SchemaError
from plexapi.server import PlexServer

# import local util modules
from util import plexutil

logger = logging.getLogger(__name__)

filename = os.path.basename(sys.argv[0])
SCRIPT_NAME = os.path.splitext(filename)[0]


class ScheduleEntry(NamedTuple):
    type: str
    startdate: datetime
    enddate: datetime
    force: bool
    path: str


ScheduleType = Dict[str, List[ScheduleEntry]]


def arguments() -> Namespace:
    """Setup and Return command line arguments
    See https://docs.python.org/3/howto/argparse.html

    Returns:
        argparse.Namespace: Namespace object
    """
    description = "Automate scheduling of pre-roll intros for Plex"
    version = "0.12.0"

    config_default = "./config.ini"
    log_config_default = "./logging.conf"
    schedule_default = "./preroll_schedules.yaml"
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


def schedule_types() -> ScheduleType:
    """Return the main types of schedules to be used for storage processing

    Returns:
        ScheduleType: Dict of main schema items
    """
    schema: ScheduleType = {
        "default": [],
        "monthly": [],
        "weekly": [],
        "date_range": [],
        "misc": [],
    }
    return schema


def week_range(year: int, weeknum: int) -> Tuple[datetime, datetime]:
    """Return the starting/ending date range of a given year/week

    Args:
        year (int):     Year to calc range for
        weeknum (int):  Month of the year (1-12)

    Returns:
        DateTime: Start date of the Year/Month
        DateTime: End date of the Year/Month
    """
    start = datetime.strptime(f"{year}-W{int(weeknum) - 1}-0", "%Y-W%W-%w").date()
    end = start + timedelta(days=6)

    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.max.time())

    return (start, end)


def month_range(year: int, monthnum: int) -> Tuple[datetime, datetime]:
    """Return the starting/ending date range of a given year/month

    Args:
        year (int):     Year to calc range for
        monthnum (int): Month of the year (1-12)

    Returns:
        DateTime: Start date of the Year/Month
        DateTime: End date of the Year/Month
    """
    start = date(year, monthnum, 1)
    next_month = start.replace(day=28) + timedelta(days=4)
    end = next_month - timedelta(days=next_month.day)

    start = datetime.combine(start, datetime.min.time())
    end = datetime.combine(end, datetime.max.time())

    return (start, end)


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

            # start parsing the Time out, for later additional processing
            dateparts = value.lower().split("-")

            year = today.year if dateparts[0] == "xxxx" else int(dateparts[0])
            month = today.month if dateparts[1] == "xx" else int(dateparts[1])

            dateparts_day = dateparts[2].split(" ")

            day = today.day if dateparts_day[0] == "xx" else int(dateparts_day[0])

            # attempt to parse out Time components
            if len(dateparts_day) > 1:
                timeparts = dateparts_day[1].split(":")
                if len(timeparts) > 1:
                    hour = now.hour if timeparts[0] == "xx" else int(timeparts[0])
                    minute = now.minute if timeparts[1] == "xx" else int(timeparts[1])
                    second = now.second + 1 if timeparts[2] == "xx" else int(timeparts[2])

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


def schedulefile_contents(schedule_filename: Optional[str]) -> dict[str, any]:  # type: ignore
    """Returns a contents of the provided YAML file and validates

    Args:
        schedule_filename (string, optional]): schedule file to load, will use defaults if not specified

    Raises:
        Validation Errors

    Returns:
        YAML Contents: YAML structure of Dict[str, Any]
    """
    default_files = ["preroll_schedules.yaml", "preroll_schedules.yml"]

    filename = None
    if schedule_filename not in ("", None):
        if os.path.exists(str(schedule_filename)):
            filename = schedule_filename
        else:
            msg = f'Pre-roll Schedule file "{schedule_filename}" not found'
            logger.error(msg)
            raise FileNotFoundError(msg)
    else:
        for f in default_files:
            if os.path.exists(f):
                filename = f
                break

    # if we still cant find a schedule file, we abort
    if not filename:
        filestr = '" / "'.join(default_files)
        logger.error('Missing schedule file: "%s"', filestr)
        raise FileNotFoundError(filestr)

    schema_filename = "util/schedulefile_schema.json"

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
        logger.error("JSON Error: %s", os.path.abspath("schedule_schema.json"), exc_info=je)
        raise
    except SchemaError as se:
        logger.error("Schema Error %s", os.path.abspath("schedule_schema.json"), exc_info=se)
        raise
    except Exception as e:
        logger.error(e, exc_info=e)
        raise

    if not v.validate(contents):  # type: ignore
        logger.error("Preroll-Schedule YAML Validation Error: %s", v.errors)  # type: ignore
        raise yaml.YAMLError(f"Preroll-Schedule YAML Validation Error: {v.errors}")  # type: ignore

    return contents


def preroll_schedule(schedule_file: Optional[str] = None) -> List[ScheduleEntry]:
    """Return a listing of defined preroll schedules for searching/use

    Args:
        schedule_file (str): path/to/schedule_preroll.yaml style config file (YAML Format)

    Raises:
        FileNotFoundError: If no schedule config file exists

    Returns:
        list: list of ScheduleEntries
    """

    contents = schedulefile_contents(schedule_file)  # type: ignore

    today = date.today()
    schedule: List[ScheduleEntry] = []
    for schedule_section in schedule_types():
        # test if section exists
        try:
            section_contents = contents[schedule_section]  # type: ignore
        except KeyError:
            logger.info('"%s" section not included in schedule file', schedule_section)
            # continue to other sections
            continue

        if schedule_section == "weekly":
            try:
                if section_contents["enabled"]:
                    for i in range(1, 53):
                        try:
                            path = str(section_contents[i])  # type: ignore

                            if path:
                                start, end = week_range(today.year, i)

                                entry = ScheduleEntry(
                                    type=schedule_section,
                                    force=False,
                                    startdate=start,
                                    enddate=end,
                                    path=path,
                                )

                                schedule.append(entry)
                        except KeyError:
                            # skip KeyError for missing Weeks
                            logger.debug(
                                'Key Value not found: "%s"->"%s", skipping week',
                                schedule_section,
                                i,
                            )
            except KeyError as ke:
                logger.error('Key Value not found in "%s" section', schedule_section, exc_info=ke)
                raise
        elif schedule_section == "monthly":
            try:
                if section_contents["enabled"]:
                    for i in range(1, 13):
                        month_abrev = date(today.year, i, 1).strftime("%b").lower()
                        try:
                            path = str(section_contents[month_abrev])  # type: ignore

                            if path:
                                start, end = month_range(today.year, i)

                                entry = ScheduleEntry(
                                    type=schedule_section,
                                    force=False,
                                    startdate=start,
                                    enddate=end,
                                    path=path,
                                )

                                schedule.append(entry)
                        except KeyError:
                            # skip KeyError for missing Months
                            logger.warning(
                                'Key Value not found: "%s"->"%s", skipping month',
                                schedule_section,
                                month_abrev,
                            )
            except KeyError as ke:
                logger.error('Key Value not found in "%s" section', schedule_section, exc_info=ke)
                raise
        elif schedule_section == "date_range":
            try:
                if section_contents["enabled"]:
                    for r in section_contents["ranges"]:  # type: ignore
                        try:
                            path = str(r["path"])  # type: ignore

                            if path:
                                try:
                                    force = r["force"]  # type: ignore
                                except KeyError as ke:
                                    # special case Optional, ignore
                                    force = False

                                start = make_datetime(r["start_date"], lowtime=True)  # type: ignore
                                end = make_datetime(r["end_date"], lowtime=False)  # type: ignore

                                entry = ScheduleEntry(
                                    type=schedule_section,
                                    force=force,  # type: ignore
                                    startdate=start,
                                    enddate=end,
                                    path=path,
                                )

                                schedule.append(entry)
                        except KeyError as ke:
                            logger.error('Key Value not found for entry: "%s"', entry, exc_info=ke)  # type: ignore
                            raise
                        except TypeError as te:
                            logger.error('Type Error "%s" Entry: "%s"', te, entry, exc_info=te)  # type: ignore
                            raise
                        except Exception as e:
                            logger.error('Exception: %s %s Entry: "%s"', type(e), e, entry, exc_info=e)  # type: ignore
                            raise
            except KeyError as ke:
                logger.error('Key Value not found in "%s" section', schedule_section, exc_info=ke)
                raise
        elif schedule_section == "misc":
            try:
                if section_contents["enabled"]:
                    try:
                        path = str(section_contents["always_use"])  # type: ignore

                        if path:
                            entry = ScheduleEntry(
                                type=schedule_section,
                                force=False,
                                startdate=datetime(today.year, today.month, today.day, 0, 0, 0),
                                enddate=datetime(today.year, today.month, today.day, 23, 59, 59),
                                path=path,
                            )

                            schedule.append(entry)
                    except KeyError as ke:
                        msg = f'Key Value not found for entry: "{entry}"'  # type: ignore
                        logger.error(msg, exc_info=ke)
                        raise
            except KeyError as ke:
                logger.error('Key Value not found in "%s" section', schedule_section, exc_info=ke)
                raise
        elif schedule_section == "default":
            try:
                if section_contents["enabled"]:
                    try:
                        path = str(section_contents["path"])  # type: ignore

                        if path:
                            entry = ScheduleEntry(
                                type=schedule_section,
                                force=False,
                                startdate=datetime(today.year, today.month, today.day, 0, 0, 0),
                                enddate=datetime(today.year, today.month, today.day, 23, 59, 59),
                                path=path,
                            )

                            schedule.append(entry)
                    except KeyError as ke:
                        logger.error('Key Value not found for entry: "%s"', entry, exc_info=ke)  # type: ignore
                        raise
            except KeyError as ke:
                logger.error('Key Value not found in "%s" section', schedule_section, exc_info=ke)
                raise
        else:
            msg = f'Unknown schedule_section "{schedule_section}" detected'
            logger.error(msg)
            raise ValueError(msg)

    # Sort list so most recent Ranges appear first
    schedule.sort(reverse=True, key=lambda x: x.startdate)

    return schedule


def build_listing_string(items: List[str], play_all: bool = False) -> str:
    """Build the Plex formatted string of preroll paths

    Args:
        items (list):               List of preroll video paths to place into a string listing
        play_all (bool, optional):  Play all videos. [Default: False (Random choice)]

    Returns:
        string: CSV Listing (, or ;) based on play_all param of preroll video paths
    """

    if len(items) == 0:
        return ";"

    if play_all:
        # use , to play all entries
        listing = ",".join(items)
    else:
        # use ; to play random selection
        listing = ";".join(items)

    return listing


def preroll_listing(schedule: List[ScheduleEntry], for_datetime: Optional[datetime] = None) -> str:
    """Return listing of preroll videos to be used by Plex

    Args:
        schedule (List[ScheduleEntry]):     List of schedule entries (See: getPrerollSchedule)
        for_datetime (datetime, optional):  Date to process pre-roll string for [Default: Today]
                                            Useful for simulating what different dates produce

    Returns:
        string: listing of preroll video paths to be used for Extras. CSV style: (;|,)
    """
    listing = ""
    entries = schedule_types()

    # determine which date to build the listing for
    if for_datetime:
        if isinstance(for_datetime, datetime):  # type: ignore
            check_datetime = for_datetime
        else:
            check_datetime = datetime.combine(for_datetime, datetime.now().time())
    else:
        check_datetime = datetime.now()

    # process the schedule for the given date
    for entry in schedule:
        try:
            entry_start = entry.startdate
            entry_end = entry.enddate
            if not isinstance(entry_start, datetime):  # type: ignore
                entry_start = datetime.combine(entry_start, datetime.min.time())
            if not isinstance(entry_end, datetime):  # type: ignore
                entry_end = datetime.combine(entry_end, datetime.max.time())

            logger.debug(
                'checking "%s" against: "%s" - "%s"', check_datetime, entry_start, entry_end
            )

            if entry_start <= check_datetime <= entry_end:
                entry_type = entry.type
                entry_path = entry.path
                entry_force = False
                try:
                    entry_force = entry.force
                except KeyError:
                    # special case Optional, ignore
                    pass

                logger.debug('Check PASS: Using "%s" - "%s"', entry_start, entry_end)

                if entry_path:
                    found = False
                    # check new schedule item against exist list
                    for e in entries[entry_type]:
                        duration_new = duration_seconds(entry_start, entry_end)
                        duration_curr = duration_seconds(e.startdate, e.enddate)

                        # only the narrowest timeframe should stay
                        # disregard if a force entry is there
                        if duration_new < duration_curr and e.force != True:
                            entries[entry_type].remove(e)

                        found = True

                    # prep for use if New, or is a force Usage
                    if not found or entry_force == True:
                        entries[entry_type].append(entry)
        except KeyError as ke:
            logger.error('KeyError with entry "%s"', entry, exc_info=ke)
            raise

    # Build the merged output based or order of Priority
    merged_list = []
    if entries["misc"]:
        merged_list.extend([p.path for p in entries["misc"]])  # type: ignore
    if entries["date_range"]:
        merged_list.extend([p.path for p in entries["date_range"]])  # type: ignore
    if entries["weekly"] and not entries["date_range"]:
        merged_list.extend([p.path for p in entries["weekly"]])  # type: ignore
    if entries["monthly"] and not entries["weekly"] and not entries["date_range"]:
        merged_list.extend([p.path for p in entries["monthly"]])  # type: ignore
    if (
        entries["default"]
        and not entries["monthly"]
        and not entries["weekly"]
        and not entries["date_range"]
    ):
        merged_list.extend([p.path for p in entries["default"]])  # type: ignore

    listing = build_listing_string(merged_list)

    return listing


def save_preroll_listing(plex: PlexServer, preroll_listing: Union[str, List[str]]) -> None:
    """Save Plex Preroll info to PlexServer settings

    Args:
        plex (PlexServer): Plex server to update
        preroll_listing (str, list[str]): csv listing or List of preroll paths to save
    """
    # if happend to send in an Iterable List, merge to a string
    if isinstance(preroll_listing, list):
        preroll_listing = build_listing_string(list(preroll_listing))

    logger.debug('Attempting save of pre-rolls: "%s"', preroll_listing)

    plex.settings.get("cinemaTrailersPrerollID").set(preroll_listing)  # type: ignore
    try:
        plex.settings.save()  # type: ignore
    except Exception as e:
        logger.error('Unable to save Pre-Rolls to Server: "%s"', plex.friendlyName, exc_info=e)  # type: ignore
        raise e

    logger.info('Saved Pre-Rolls: Server: "%s" Pre-Rolls: "%s"', plex.friendlyName, preroll_listing)  # type: ignore


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

    schedule = preroll_schedule(args.schedule_file)
    prerolls = preroll_listing(schedule)

    if args.do_test_run:
        msg = f"Test Run of Plex Pre-Rolls: **Nothing being saved**\n{prerolls}\n"
        logger.debug(msg)
        print(msg)
    else:
        save_preroll_listing(plex, prerolls)
