from datetime import datetime, date

import holidays
from holidays import HolidayBase


def _get_country_from_alpha2(alpha2: str, year: int, subdivision: str = None) -> HolidayBase:
    """
    Retrieve the HolidayBase subclass for a given country alpha-2 code.

    :param alpha2: The ISO 3166-1 alpha-2 country code.
    :param year: The year for which to retrieve holidays.
    :param subdivision: The subdivision code (e.g., state or province) if applicable.
    :return: The HolidayBase subclass for the specified country.
    :raises ValueError: If the country code is not found.
    """
    country = holidays.country_holidays(country=alpha2, years=year, subdiv=subdivision)

    if country is None:
        raise ValueError(f"Country with alpha-2 code '{alpha2}' and subdivision '{subdivision}' not found.")

    return country


# https://holidays.readthedocs.io/en/latest/examples/#date-from-holiday-name
def get_date_from_holiday_name(country_alpha2: str,
                               holiday_name: str,
                               year: int = None,
                               country_subdivision: str = None,
                               name_match_exact: bool = False) -> list[date]:
    """
    Get the date(s) of a holiday by its name for a specific country and year.

    :param country_alpha2: The ISO 3166-1 alpha-2 country code.
    :param holiday_name: The name of the holiday to look for (case-insensitive).
    :param year: The year to search for the holiday. Defaults to the current year if None.
    :param country_subdivision: The subdivision code (e.g., state or province) if applicable.
    :param name_match_exact: If True, matches the holiday name exactly; otherwise, allows partial matches.
    :return: A sorted list of dates when the holiday occurs in the specified year.
    """
    year = year or datetime.now().year
    country_instance = _get_country_from_alpha2(alpha2=country_alpha2, year=year, subdivision=country_subdivision)

    dates = country_instance.get_named(holiday_name=holiday_name, lookup="iexact" if name_match_exact else "icontains")

    return sorted(dates)
