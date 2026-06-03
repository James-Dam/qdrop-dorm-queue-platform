import unittest

from app.booking_utils import generate_time_slot_groups, local_time_to_utc_datetime


class BookingUtilsTests(unittest.TestCase):
    def test_generate_time_slot_groups_creates_48_slots(self):
        def always_available(item_id, time_slot):
            return True

        groups = generate_time_slot_groups(always_available, 1)
        total_slots = sum(len(group) for group in groups.values())

        self.assertEqual(total_slots, 48)
        self.assertEqual(groups["early_morning"][0]["db_value"], "00:00")
        self.assertTrue(groups["early_morning"][0]["available"])

    def test_local_time_to_utc_datetime_returns_utc_datetime(self):
        utc_dt = local_time_to_utc_datetime("12:00", "America/New_York")
        self.assertIsNotNone(utc_dt.tzinfo)
        self.assertEqual(utc_dt.utcoffset().total_seconds(), 0)
        self.assertTrue(utc_dt.isoformat().endswith("+00:00"))


if __name__ == "__main__":
    unittest.main()
