import enum
from datetime import datetime

from flask import (
    request as flask_request,
)
from pydantic import BaseModel, Field


class Timeframe(enum.Enum):
    seconds = "s"
    minutes = "m"
    hours = "h"
    days = "d"


def parse_timeframe(timeframe: str) -> tuple[int, Timeframe]:
    """
    Parse the timeframe string into a tuple of an integer and a Timeframe enum.
    ex. 24h -> (24, Timeframe.hours), 5m -> (5, Timeframe.minutes)
    """
    if not timeframe or len(timeframe) < 2:
        raise ValueError("Invalid timeframe format. Expected format: <number><unit> (e.g., 24h, 5m).")

    try:
        number = int(timeframe[:-1])
    except ValueError:
        raise ValueError("Invalid number in timeframe.")

    unit = timeframe[-1].lower()
    if unit == 's':
        return number, Timeframe.seconds
    elif unit == 'm':
        return number, Timeframe.minutes
    elif unit == 'h':
        return number, Timeframe.hours
    elif unit == 'd':
        return number, Timeframe.days
    else:
        raise ValueError("Invalid timeframe unit. Use 's', 'm', 'h', or 'd'.")


def seconds_between(start: datetime, end: datetime = None) -> int:
    """
    Calculate the number of seconds between two datetime objects.
    :param start: The start datetime.
    :param end: The end datetime.
    :return: The number of seconds between the two datetimes.
    """
    end = end or datetime.now()
    return int((end - start).total_seconds())


def minutes_between(start: datetime, end: datetime = None) -> int:
    """
    Calculate the number of minutes between two datetime objects.
    :param start: The start datetime.
    :param end: The end datetime.
    :return: The number of minutes between the two datetimes.
    """
    return seconds_between(start, end) // 60


def hours_between(start: datetime, end: datetime = None) -> int:
    """
    Calculate the number of hours between two datetime objects.
    :param start: The start datetime.
    :param end: The end datetime.
    :return: The number of hours between the two datetimes.
    """
    return seconds_between(start, end) // 3600


def days_between(start: datetime, end: datetime = None) -> int:
    """
    Calculate the number of days between two datetime objects.
    :param start: The start datetime.
    :param end: The end datetime.
    :return: The number of days between the two datetimes.
    """
    return seconds_between(start, end) // 86400


class LastRunWithinTimeframeCheck(BaseModel):
    timeframe_number: int = Field(..., description="The numeric part of the timeframe (e.g., 24 in 24h).")
    timeframe_unit: Timeframe = Field(..., description="The unit of the timeframe (e.g., hours in 24h).")

    @classmethod
    def from_flask_request(cls, request: flask_request):
        """
        Create an instance from a Flask request.
        """
        timeframe = request.args.get('timeframe')

        if not timeframe:
            raise ValueError("Timeframe parameter is required.")

        try:
            number, unit = parse_timeframe(timeframe)
            return cls(timeframe_number=number, timeframe_unit=unit)
        except ValueError as e:
            raise ValueError(f"Could not parse timeframe: {e}")

    def is_within_timeframe(self, time: datetime) -> bool:
        """
        Check if the given time is within the specified timeframe.
        :param time: The datetime to check against.
        :return: True if the time is within the timeframe, False otherwise.
        """
        if self.timeframe_unit == Timeframe.seconds:
            return seconds_between(time) <= self.timeframe_number
        elif self.timeframe_unit == Timeframe.minutes:
            return minutes_between(time) <= self.timeframe_number
        elif self.timeframe_unit == Timeframe.hours:
            return hours_between(time) <= self.timeframe_number
        elif self.timeframe_unit == Timeframe.days:
            return days_between(time) <= self.timeframe_number
        else:
            raise ValueError("Invalid timeframe unit.")
