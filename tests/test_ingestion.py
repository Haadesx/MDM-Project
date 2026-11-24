import unittest
from dataclasses import replace
from datetime import date, datetime, timezone

from cooperalink.domain import DataContractError
from cooperalink.ingestion import canonical_pair, deduplicate_events, normalize_event
from tests.helpers import COUNTRIES, fixture_events, raw_events


class IngestionContractTests(unittest.TestCase):
    def test_pair_is_undirected_and_canonical(self):
        self.assertEqual(canonical_pair("USA", "CAN"), ("CAN", "USA"))
        self.assertEqual(canonical_pair("CAN", "USA"), ("CAN", "USA"))

    def test_self_pair_is_invalid(self):
        with self.assertRaises(DataContractError):
            canonical_pair("USA", "USA")

    def test_parse_exact_061_and_utc_date(self):
        row = raw_events()[0]
        parsed = normalize_event(row, COUNTRIES)
        self.assertEqual(parsed, fixture_events()[0])
        self.assertEqual(parsed.added_at.tzinfo, timezone.utc)

    def test_integer_event_code_is_rejected_not_repaired(self):
        row = dict(raw_events()[0], EventCode=61)
        with self.assertRaises(DataContractError):
            normalize_event(row, COUNTRIES)

    def test_neighboring_event_codes_are_excluded(self):
        for code in ("060", "0611", "071"):
            with self.subTest(code=code):
                self.assertIsNone(normalize_event(dict(raw_events()[0], EventCode=code), COUNTRIES))

    def test_actor_country_fields_are_used_not_geolocation(self):
        row = dict(raw_events()[0], Actor1CountryCode="USA", Actor2CountryCode="IND",
                   Actor1Geo_CountryCode="CA", Actor2Geo_CountryCode="AS")
        self.assertEqual(normalize_event(row, COUNTRIES).pair, ("IND", "USA"))

    def test_unknown_blank_and_domestic_actors_are_excluded(self):
        for a, b in (("EUR", "USA"), ("", "USA"), ("USA", "USA")):
            with self.subTest(pair=(a,b)):
                row = dict(raw_events()[0], Actor1CountryCode=a, Actor2CountryCode=b)
                self.assertIsNone(normalize_event(row, COUNTRIES))

    def test_late_report_preserves_occurrence_but_observed_day_is_added_day(self):
        parsed = normalize_event(raw_events()[8], COUNTRIES)
        self.assertEqual(parsed.event_day, date(2024, 1, 10))
        self.assertEqual(parsed.observed_day, date(2024, 2, 5))

    def test_duplicate_rows_and_permutation_leave_identity_unchanged(self):
        events = fixture_events()
        once = deduplicate_events(events)
        repeated = deduplicate_events(tuple(reversed(events)) + (events[0], events[0]))
        self.assertEqual(once, repeated)
        self.assertEqual(len(once), 9)

    def test_conflicting_same_id_is_rejected(self):
        first = fixture_events()[0]
        changed = replace(first, added_at=datetime(2024, 1, 3, tzinfo=timezone.utc))
        with self.assertRaises(DataContractError):
            deduplicate_events((first, changed))

    def test_malformed_calendar_dates_are_rejected(self):
        for field, value in (("DATEADDED", "20240230000000"), ("SQLDATE", "20241301")):
            with self.subTest(field=field):
                with self.assertRaises(DataContractError):
                    normalize_event(dict(raw_events()[0], **{field:value}), COUNTRIES)

