import unittest
from datetime import date, timedelta

from cooperalink.domain import CoverageError, LeakageError
from cooperalink.temporal import (
    annual_folds, assert_chronology, daily_counts, date_window, link_label, persistence,
)
from tests.helpers import ORIGIN, complete_days, event, fixture_events


class TemporalContractTests(unittest.TestCase):
    def test_context_is_exactly_90_inclusive_days(self):
        days = date_window(ORIGIN, 90)
        self.assertEqual(len(days), 90)
        self.assertEqual(days[0], date(2023, 11, 3))
        self.assertEqual(days[-1], ORIGIN)
        self.assertEqual(len(set(days)), 90)

    def test_counts_use_added_day_zero_fill_and_distinct_ids(self):
        days = (date(2024,1,1), date(2024,1,2), date(2024,1,31))
        rows = fixture_events()
        self.assertEqual(daily_counts(rows+(rows[0],), ("AUS","CAN"), days, complete_days()), (0,1,1))

    def test_different_ids_for_reciprocal_records_are_distinct_counts(self):
        rows = (event("1","AUS","CAN","2024-01-31"), event("2","AUS","CAN","2024-01-31"))
        self.assertEqual(daily_counts(rows,("AUS","CAN"),(ORIGIN,),complete_days()), (2,))

    def test_unverified_empty_day_is_not_imputed_to_zero(self):
        missing = complete_days() - {ORIGIN}
        with self.assertRaises(CoverageError):
            daily_counts((), ("AUS","CAN"), (ORIGIN,), missing)

    def test_label_includes_first_and_last_forecast_days_only(self):
        cov = complete_days()
        self.assertEqual(link_label(fixture_events(),("CAN","USA"),ORIGIN,cov),1)  # Feb 1
        self.assertEqual(link_label(fixture_events(),("AUS","USA"),ORIGIN,cov),1)  # Mar 1
        self.assertEqual(link_label(fixture_events(),("AUS","CAN"),ORIGIN,cov),0)  # Jan 31 excluded
        self.assertEqual(link_label(fixture_events(),("AUS","IND"),ORIGIN,cov),0)  # Mar 2 excluded

    def test_late_occurrence_counts_in_future_observation_target(self):
        late_only = (fixture_events()[8],)
        self.assertEqual(link_label(late_only, ("IND","USA"), ORIGIN, complete_days()), 1)
        self.assertEqual(persistence(late_only, ("IND","USA"), ORIGIN, complete_days()), 0)

    def test_persistence_has_exact_30_day_boundaries(self):
        cov = complete_days()
        self.assertEqual(persistence(fixture_events(),("AUS","CAN"),ORIGIN,cov),1)  # Jan 2 & 31
        self.assertEqual(persistence(fixture_events(),("AUS","IND"),ORIGIN,cov),0)  # Jan 1 too old

    def test_persistence_includes_lower_boundary_without_a_later_record(self):
        # A newer event must not conceal an off-by-one error at T-29.
        lower_only = (event("boundary", "AUS", "CAN", "2024-01-02"),)
        self.assertEqual(persistence(lower_only,("AUS","CAN"),ORIGIN,complete_days()),1)

    def test_future_injection_cannot_change_persistence_or_context_counts(self):
        historical = tuple(e for e in fixture_events() if e.observed_day <= ORIGIN)
        injected = historical + (event("999", "AUS", "USA", "2024-02-01"),)
        cov = complete_days()
        days = tuple(ORIGIN-timedelta(days=i) for i in reversed(range(90)))
        self.assertEqual(persistence(historical,("AUS","USA"),ORIGIN,cov),
                         persistence(injected,("AUS","USA"),ORIGIN,cov))
        self.assertEqual(daily_counts(historical,("AUS","USA"),days,cov),
                         daily_counts(injected,("AUS","USA"),days,cov))

    def test_label_requires_complete_future_coverage_even_if_positive_found(self):
        cov = complete_days() - {date(2024, 2, 20)}
        with self.assertRaises(CoverageError):
            link_label(fixture_events(),("CAN","USA"),ORIGIN,cov)

    def test_leap_year_has_twelve_nonoverlapping_complete_folds(self):
        folds = annual_folds(2024)
        self.assertEqual(len(folds), 12)
        self.assertEqual(folds[0].origin, date(2023,12,31))
        self.assertEqual(folds[0].label_start, date(2024,1,1))
        self.assertEqual(folds[-1].label_end, date(2024,12,25))
        for a,b in zip(folds, folds[1:]):
            self.assertEqual(a.label_end + timedelta(days=1), b.label_start)
        self.assertTrue(all((f.label_end-f.label_start).days == 29 for f in folds))

    def test_nonleap_year_tail_and_phase_boundaries_are_explicit(self):
        for year in (2021,2022,2023):
            folds = annual_folds(year)
            self.assertEqual(len(folds),12)
            self.assertEqual(folds[-1].label_end,date(year,12,26))
            self.assertTrue(all(f.label_end.year==year for f in folds))

    def test_fitted_labels_must_mature_before_origin(self):
        self.assertIsNone(assert_chronology((date(2023,12,26),date(2023,12,31)),date(2023,12,31)))
        with self.assertRaises(LeakageError):
            assert_chronology((date(2024,1,1),),date(2023,12,31))

