import random
from datetime import datetime
from typing import NamedTuple, List, Union

import modules.logs as logging
from modules import utils
from modules.statics import ScheduleType


class ScheduleEntry(NamedTuple):
    type: str
    start_date: datetime
    end_date: datetime
    paths: List[str]
    weight: int
    name_prefix: str

    @property
    def should_be_used(self) -> bool:
        now = datetime.now()
        return self.start_date <= now <= self.end_date

    @property
    def name(self) -> str:
        return f"{self.name_prefix} ({self.start_date} - {self.end_date})"


def schedule_entry_from_always(paths: List[str], count: int, weight: int) -> ScheduleEntry:
    start_date = utils.make_midnight(utils.start_of_time())
    end_date = utils.make_right_before_midnight(utils.end_of_time())

    if count > len(paths):
        logging.warning(f"Always schedule has a count of {count} but only {len(paths)} paths were provided. "
                        f"Setting count to {len(paths)}")
        count = len(paths)

    random_paths = random.sample(population=paths, k=count)

    return ScheduleEntry(type=ScheduleType.always.value,
                         start_date=start_date,
                         end_date=end_date,
                         paths=random_paths,
                         weight=weight,
                         name_prefix="Always")


def schedule_entry_from_week_number(week_number: int, paths: List[str], weight: int) -> Union[ScheduleEntry, None]:
    start_date = utils.start_of_week_number(week_number=week_number)
    end_date = utils.end_of_week_number(week_number=week_number)

    return ScheduleEntry(type=ScheduleType.weekly.value,
                         start_date=start_date,
                         end_date=end_date,
                         paths=paths,
                         weight=weight,
                         name_prefix=f"Week {week_number}")


def schedule_entry_from_month_number(month_number: int, paths: List[str], weight: int) -> Union[ScheduleEntry, None]:
    start_date = utils.start_of_month(month_number=month_number)
    end_date = utils.end_of_month(month_number=month_number)

    return ScheduleEntry(type=ScheduleType.monthly.value,
                         start_date=start_date,
                         end_date=end_date,
                         paths=paths,
                         weight=weight,
                         name_prefix=f"Month {month_number}")


def schedule_entry_from_date_range(start_date_string: str, end_date_string: str, paths: List[str], weight: int,
                                   name: str = None) \
        -> Union[ScheduleEntry, None]:
    if not name:
        name = "Date Range"

    start_date, end_date = utils.wildcard_strings_to_datetimes(start_date_string=start_date_string,
                                                               end_date_string=end_date_string)

    if not start_date or not end_date:
        logging.error(
            f"{name} has invalid start or end date wildcard patterns. "
            f"Any wildcard elements must be in the same position in both the start and end date.\n"
            f"Start date: {start_date_string}\nEnd date: {end_date_string}")
        return None

    return ScheduleEntry(type=ScheduleType.date_range.value,
                         start_date=start_date,
                         end_date=end_date,
                         paths=paths,
                         weight=weight,
                         name_prefix=name)
