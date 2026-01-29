import unittest


class TestHolidays(unittest.TestCase):
    def test_create_schedule_entry_from_floating_holiday(self):
        from modules.models import schedule_entry_from_date_range, ScheduleType
        from modules.config_parser import FloatingHolidayConfig
        from modules import utils

        floating_holiday_config = FloatingHolidayConfig(
            data={
                "name": "Thanksgiving",
                "country": "US",
            }
        )

        paths = ["/media/holiday1", "/media/holiday2"]
        weight = 10
        disable_always = False
        name = "Thanksgiving Schedule"

        schedule_entry = schedule_entry_from_date_range(
            start_date_string=None,
            end_date_string=None,
            holiday=floating_holiday_config,
            paths=paths,
            weight=weight,
            name=name,
            disable_always=disable_always
        )

        self.assertEqual(schedule_entry.type, ScheduleType.date_range.value)
        self.assertEqual(schedule_entry.paths, paths)
        self.assertEqual(schedule_entry.weight, weight)
        self.assertEqual(schedule_entry.disable_always, disable_always)
        self.assertIn(name, schedule_entry.name_prefix)

        # Dates should be between YYYY-11-22 and YYYY-11-28 for Thanksgiving (4th Thursday of November)
        current_year = utils.now().year
        self.assertEqual(schedule_entry.start_date.year, current_year)
        self.assertEqual(schedule_entry.start_date.month, 11)
        self.assertTrue(22 <= schedule_entry.start_date.day <= 28)
        self.assertEqual(schedule_entry.start_date.weekday(), 3)  # Thursday
        self.assertEqual(schedule_entry.end_date.year, current_year)
        self.assertEqual(schedule_entry.end_date.month, 11)
        self.assertTrue(22 <= schedule_entry.end_date.day <= 28)
        self.assertEqual(schedule_entry.end_date.weekday(), 3)  # Thursday

    def test_create_schedule_entry_from_invalid_floating_holiday(self):
        from modules.models import schedule_entry_from_date_range
        from modules.config_parser import FloatingHolidayConfig

        floating_holiday_config = FloatingHolidayConfig(
            data={
                "name": "NonExistentHoliday",
                "country": "US",
            }
        )

        paths = ["/media/holiday1", "/media/holiday2"]
        weight = 10
        name = "Invalid Holiday Schedule"

        schedule_entry = schedule_entry_from_date_range(
                start_date_string=None,
                end_date_string=None,
                holiday=floating_holiday_config,
                paths=paths,
                weight=weight,
                name=name
            )

        self.assertIsNone(schedule_entry)
        # Logs should include an INFO about the holiday not being found.

    def test_create_schedule_entry_from_floating_holiday_invalid_country(self):
        from modules.models import schedule_entry_from_date_range
        from modules.config_parser import FloatingHolidayConfig

        floating_holiday_config = FloatingHolidayConfig(
            data={
                "name": "Thanksgiving",
                "country": "XX",  # Invalid country code
            }
        )

        paths = ["/media/holiday1", "/media/holiday2"]
        weight = 10
        name = "Invalid Country Holiday Schedule"

        schedule_entry = schedule_entry_from_date_range(
            start_date_string=None,
            end_date_string=None,
            holiday=floating_holiday_config,
            paths=paths,
            weight=weight,
            name=name
        )

        self.assertIsNone(schedule_entry)
        # Logs should include an ERROR about the invalid country code, and an INFO about the holiday not being found.