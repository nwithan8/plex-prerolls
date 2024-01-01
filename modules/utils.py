from datetime import datetime, timedelta, date
from typing import Tuple, Union

from pytz import timezone

import modules.logs as logging


def make_plural(word, count: int, suffix_override: str = 's') -> str:
    if count > 1:
        return f"{word}{suffix_override}"
    return word


def quote(string: str) -> str:
    return f"\"{string}\""


def status_code_is_success(status_code: int) -> bool:
    return 200 <= status_code < 300


def milliseconds_to_minutes_seconds(milliseconds: int) -> str:
    seconds = int(milliseconds / 1000)
    minutes = int(seconds / 60)
    if minutes < 10:
        minutes = f"0{minutes}"
    seconds = int(seconds % 60)
    if seconds < 10:
        seconds = f"0{seconds}"
    return f"{minutes}:{seconds}"


def now(timezone_code: str = None) -> datetime:
    if timezone_code:
        return datetime.now(timezone(timezone_code))  # will raise exception if invalid timezone_code
    return datetime.now()


def now_plus_milliseconds(milliseconds: int, timezone_code: str = None) -> datetime:
    if timezone_code:
        _now = datetime.now(timezone(timezone_code))  # will raise exception if invalid timezone_code
    else:
        _now = datetime.now()
    return _now + timedelta(milliseconds=milliseconds)


def now_in_range(start: datetime, end: datetime) -> bool:
    _now = now()
    return start <= _now <= end


def start_of_time() -> datetime:
    return datetime(1970, 1, 1)


def end_of_time() -> datetime:
    return datetime(9999, 12, 31)


def start_of_year(year: int = None) -> datetime:
    _now = now()

    if not year:
        year = _now.year

    return datetime(year, 1, 1)


def end_of_year(year: int = None) -> datetime:
    _now = now()

    if not year:
        year = _now.year

    return datetime(year, 12, 31)


def start_of_month(month_number: int = None) -> datetime:
    _now = now()

    if not month_number:
        month_number = _now.month

    return datetime(_now.year, month_number, 1)


def end_of_month(month_number: int = None) -> datetime:
    _now = now()

    if not month_number:
        month_number = _now.month

    if month_number == 12:
        return end_of_year(year=_now.year)  # If month is December, return end of year (shortcut)
    else:
        return start_of_month(month_number=month_number + 1) - timedelta(
            days=1)  # Subtract one day from start of next month


def start_of_week_number(week_number: int = None) -> datetime:
    _now = now()

    if not week_number:
        week_number = _now.strftime('%U')

    return datetime.strptime(f"{_now.year}-W{int(week_number)}-0", "%Y-W%W-%w")


def end_of_week_number(week_number: int = None) -> datetime:
    _now = now()

    if not week_number:
        week_number = _now.strftime('%U')

    return datetime.strptime(f"{_now.year}-W{int(week_number)}-6", "%Y-W%W-%w")


def make_midnight(date: datetime) -> datetime:
    return datetime(date.year, date.month, date.day)


def make_right_before_midnight(date: datetime) -> datetime:
    return datetime(date.year, date.month, date.day, 23, 59, 59)


def limit_text_length(text: str, limit: int, suffix: str = "...") -> str:
    if len(text) <= limit:
        return text

    suffix_length = len(suffix)
    return f"{text[:limit - suffix_length]}{suffix}"


def string_to_datetime(date_string: str, template: str = "%Y-%m-%dT%H:%M:%S") -> datetime:
    """
    Convert a datetime string to a datetime.datetime object

    :param date_string: datetime string to convert
    :type date_string: str
    :param template: (Optional) datetime template to use when parsing string
    :type template: str, optional
    :return: datetime.datetime object
    :rtype: datetime.datetime
    """
    if date_string.endswith('Z'):
        date_string = date_string[:-5]
    return datetime.strptime(date_string, template)


def datetime_to_string(datetime_object: datetime, template: str = "%Y-%m-%dT%H:%M:%S.000Z") -> str:
    """
    Convert a datetime.datetime object to a string

    :param datetime_object: datetime.datetime object to convert
    :type datetime_object: datetime.datetime
    :param template: (Optional) datetime template to use when parsing string
    :type template: str, optional
    :return: str representation of datetime
    :rtype: str
    """
    return datetime_object.strftime(template)


def wildcard_strings_to_datetimes(start_date_string: str, end_date_string: str) -> \
        Tuple[Union[datetime, None], Union[datetime, None]]:
    """
    Convert date or datetime strings with wildcards to datetime.datetime objects

    :param start_date_string: start datetime string to convert
    :type start_date_string: str
    :param end_date_string: end datetime string to convert
    :type end_date_string: str
    :return: datetime.datetime object
    :rtype: datetime.datetime
    """
    if isinstance(start_date_string, date):
        start_date_string = start_date_string.strftime("%Y-%m-%d")
    if isinstance(end_date_string, date):
        end_date_string = end_date_string.strftime("%Y-%m-%d")

    start_date_and_time = start_date_string.split(' ')
    end_date_and_time = end_date_string.split(' ')
    template = "%Y-%m-%d %H:%M:%S"
    _now = now()

    # Sample: xxxx-xx-xx
    # Sample: xxxx-xx-xx xx:xx:xx

    _start_date = start_date_and_time[0]  # xxxx-xx-xx
    _end_date = end_date_and_time[0]  # xxxx-xx-xx

    need_specific_datetime = False

    _start_time = start_date_and_time[1] if len(start_date_and_time) > 1 else "00:00:00"
    _end_time = end_date_and_time[1] if len(end_date_and_time) > 1 else "23:59:59"

    # Sample: xxxx-xx-xx xx:xx:xx

    start_time_parts = _start_time.split(':')
    end_time_parts = _end_time.split(':')

    start_second = start_time_parts[2]
    end_second = end_time_parts[2]

    # Can't have a wildcard in one and not the other
    if (start_second != 'xx' and end_second == 'xx') or (start_second == 'xx' and end_second != 'xx'):
        logging.error(message=f"Incompatible second comparison: {start_date_string} - {end_date_string}")
        return None, None

    # At this point, either they both have wildcards or neither do, we can assume based on start_second
    if start_second == 'xx':
        start_second = '00'
        end_second = '59'  # Keep wide to ensure script running time doesn't interfere
    else:
        need_specific_datetime = True

    # Finalize the seconds
    start_second = int(start_second)
    end_second = int(end_second)

    start_minute = start_time_parts[1]
    end_minute = end_time_parts[1]

    # Can't have a wildcard in one and not the other
    if (start_minute != 'xx' and end_minute == 'xx') or (start_minute == 'xx' and end_minute != 'xx'):
        logging.error(message=f"Incompatible minute comparison: {start_date_string} - {end_date_string}")
        return None, None

    # At this point, either they both have wildcards or neither do, we can assume based on start_minute
    if start_minute == 'xx':
        if need_specific_datetime:
            start_minute = _now.minute
            end_minute = _now.minute + 3  # Give buffer for script running time
        else:
            start_minute = '00'
            end_minute = '59'  # Keep wide to ensure script running time doesn't interfere
    else:
        need_specific_datetime = True

    # Finalize the minutes
    start_minute = int(start_minute)
    end_minute = int(end_minute)

    start_hour = start_time_parts[0]
    end_hour = end_time_parts[0]

    # Can't have a wildcard in one and not the other
    if (start_hour != 'xx' and end_hour == 'xx') or (start_hour == 'xx' and end_hour != 'xx'):
        logging.error(message=f"Incompatible hour comparison: {start_date_string} - {end_date_string}")
        return None, None

    # At this point, either they both have wildcards or neither do, we can assume based on start_hour
    if start_hour == 'xx':
        if need_specific_datetime:
            start_hour = _now.hour
            end_hour = _now.hour
        else:
            start_hour = '00'
            end_hour = '23'  # Keep wide to ensure script running time doesn't interfere

    # Finalize the hours
    start_hour = int(start_hour)
    end_hour = int(end_hour)

    _start_time = f"{start_hour}:{start_minute}:{start_second}"
    _end_time = f"{end_hour}:{end_minute}:{end_second}"

    start_date_parts = _start_date.split('-')
    end_date_parts = _end_date.split('-')

    start_day = start_date_parts[2]
    end_day = end_date_parts[2]

    # Can't have a wildcard in one and not the other
    if (start_day != 'xx' and end_day == 'xx') or (start_day == 'xx' and end_day != 'xx'):
        logging.error(message=f"Incompatible day comparison: {start_date_string} - {end_date_string}")
        return None, None

    # At this point, either they both have wildcards or neither do, we can assume based on start_day
    if start_day == 'xx':
        start_day = _now.day
        end_day = _now.day
    else:
        need_specific_datetime = True

    # Finalize the days
    start_day = int(start_day)
    end_day = int(end_day)

    start_month = start_date_parts[1]
    end_month = end_date_parts[1]

    # Can't have a wildcard in one and not the other
    if (start_month != 'xx' and end_month == 'xx') or (start_month == 'xx' and end_month != 'xx'):
        logging.error(message=f"Incompatible month comparison: {start_date_string} - {end_date_string}")
        return None, None

    # At this point, either they both have wildcards or neither do, we can assume based on start_month
    if start_month == 'xx':
        if need_specific_datetime:
            start_month = _now.month
            end_month = _now.month

            # Account for crossing a month boundary
            if start_day > end_day:  # e.g. Start on the 31st and end on the 1st
                if _now.day < start_day:  # Current date is before start day (in the next month)
                    start_month -= 1  # TODO: This could break if the start_month is January (1) -> 0
                else:
                    end_month += 1  # TODO: This could break if the end_month is December (12) -> 13
        else:
            start_month = start_of_year().month
            end_month = end_of_year().month
    else:
        need_specific_datetime = True

    # Finalize the months
    start_month = int(start_month)
    end_month = int(end_month)

    start_year = start_date_parts[0]
    end_year = end_date_parts[0]

    # Can't have a wildcard in one and not the other
    if (start_year != 'xxxx' and end_year == 'xxxx') or (start_year == 'xxxx' and end_year != 'xxxx'):
        logging.error(message=f"Incompatible year comparison: {start_date_string} - {end_date_string}")
        return None, None

    # At this point, either they both have wildcards or neither do, we can assume based on start_year
    if start_year == 'xxxx':
        if need_specific_datetime:
            start_year = _now.year
            end_year = _now.year

            # Account for crossing a year boundary
            # At this point, the start_month and end_month are numerical strings or ints
            if start_month > end_month:  # e.g. Start in December (12) and end in January (1)
                if _now.month < start_month:  # Current date is before start month (in the next year)
                    start_year -= 1
                else:
                    end_year += 1
        else:
            start_year = start_of_time().year
            end_year = end_of_time().year

    # Finalize the years
    start_year = int(start_year)
    end_year = int(end_year)

    _start_date = f"{start_year}-{start_month}-{start_day}"
    _end_date = f"{end_year}-{end_month}-{end_day}"

    _start_datetime = f"{_start_date} {_start_time}"
    _end_datetime = f"{_end_date} {_end_time}"

    return string_to_datetime(date_string=_start_datetime, template=template), \
        string_to_datetime(date_string=_end_datetime, template=template)
