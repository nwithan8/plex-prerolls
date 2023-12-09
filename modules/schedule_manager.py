from typing import List

from modules import models
from modules.config_parser import (
    Config,
)
from modules.models import ScheduleEntry
import modules.logs as logging


class ScheduleManager:
    def __init__(self, config: Config):
        self._config = config
        self.weekly_schedules: List[ScheduleEntry] = []
        self.monthly_schedules: List[ScheduleEntry] = []
        self.date_range_schedules: List[ScheduleEntry] = []
        self.always_schedules: List[ScheduleEntry] = []
        self._parse_schedules()  # Only call this once, otherwise it will duplicate schedules

    def _parse_schedules(self):
        logging.info("Parsing schedules...")
        if self._config.weekly.enabled:
            for week in self._config.weekly.weeks:
                self.weekly_schedules.append(models.schedule_entry_from_week_number(week_number=week.number,
                                                                                    paths=week.paths,
                                                                                    weight=week.weight))

        if self._config.monthly.enabled:
            for month in self._config.monthly.months:
                self.monthly_schedules.append(models.schedule_entry_from_month_number(month_number=month.number,
                                                                                      paths=month.paths,
                                                                                      weight=month.weight))
        if self._config.date_ranges.enabled:
            for date_range in self._config.date_ranges.ranges:
                entry = models.schedule_entry_from_date_range(start_date_string=date_range.start_date,
                                                              end_date_string=date_range.end_date,
                                                              paths=date_range.paths,
                                                              weight=date_range.weight,
                                                              name=date_range.name)
                if entry:
                    self.date_range_schedules.append(entry)

        if self._config.always.enabled:
            self.always_schedules.append(models.schedule_entry_from_always(paths=self._config.always.paths,
                                                                           count=self._config.always.random_count,
                                                                           weight=self._config.always.weight))

    @property
    def valid_weekly_schedules(self) -> List[ScheduleEntry]:
        return [schedule for schedule in self.weekly_schedules if schedule.should_be_used]

    @property
    def valid_weekly_schedule_count(self) -> int:
        return len(self.valid_weekly_schedules)

    @property
    def valid_weekly_schedule_log_message(self) -> str:
        valid_schedules = ""
        for schedule in self.valid_weekly_schedules:
            valid_schedules += f"- {schedule.name}\n"
        return valid_schedules

    @property
    def valid_monthly_schedules(self) -> List[ScheduleEntry]:
        return [schedule for schedule in self.monthly_schedules if schedule.should_be_used]

    @property
    def valid_monthly_schedule_count(self) -> int:
        return len(self.valid_monthly_schedules)

    @property
    def valid_monthly_schedule_log_message(self) -> str:
        valid_schedules = ""
        for schedule in self.valid_monthly_schedules:
            valid_schedules += f"- {schedule.name}\n"
        return valid_schedules

    @property
    def valid_date_range_schedules(self) -> List[ScheduleEntry]:
        return [schedule for schedule in self.date_range_schedules if schedule.should_be_used]

    @property
    def valid_date_range_schedule_count(self) -> int:
        return len(self.valid_date_range_schedules)

    @property
    def valid_date_range_schedule_log_message(self) -> str:
        valid_schedules = ""
        for schedule in self.valid_date_range_schedules:
            valid_schedules += f"- {schedule.name}\n"
        return valid_schedules

    @property
    def valid_always_schedules(self) -> List[ScheduleEntry]:
        return [schedule for schedule in self.always_schedules if schedule.should_be_used]

    @property
    def valid_always_schedule_count(self) -> int:
        return len(self.valid_always_schedules)

    @property
    def valid_always_schedule_log_message(self) -> str:
        valid_schedules = ""
        for schedule in self.valid_always_schedules:
            valid_schedules += f"- {schedule.name}\n"
        return valid_schedules

    @property
    def all_schedules(self) -> List[ScheduleEntry]:
        return self.always_schedules + self.weekly_schedules + self.monthly_schedules + self.date_range_schedules

    @property
    def all_valid_schedules(self) -> List[ScheduleEntry]:
        return [schedule for schedule in self.all_schedules if schedule.should_be_used]

    @property
    def all_valid_paths(self) -> List[str]:
        """
        Returns a list of all valid paths from all valid schedules. Accounts for weight.
        """
        paths = []
        for schedule in self.all_valid_schedules:
            for _ in range(schedule.weight):
                paths.extend(schedule.paths)

        return paths

    @property
    def valid_schedule_count(self) -> int:
        return len(self.all_valid_schedules)

    @property
    def valid_schedule_count_log_message(self) -> str:
        return f"""
Valid Schedule Count:
Always - {self.valid_always_schedule_count}
{self.valid_always_schedule_log_message}
Weekly - {self.valid_weekly_schedule_count}
{self.valid_weekly_schedule_log_message}
Monthly - {self.valid_monthly_schedule_count}
{self.valid_monthly_schedule_log_message}
Date Ranges - {self.valid_date_range_schedule_count}
{self.valid_date_range_schedule_log_message}"""
