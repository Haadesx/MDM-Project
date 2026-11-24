import unittest

from cooperalink.domain import DataContractError
from cooperalink.universe import candidate_pairs, select_countries, validate_prediction_keys
from tests.helpers import COUNTRIES, event


class UniverseContractTests(unittest.TestCase):
    def test_country_selection_uses_2020_only_and_lexical_ties(self):
        history = (
            event("1", "AUS", "CAN", "2020-01-01"),
            event("2", "CAN", "IND", "2020-02-01"),
            event("3", "IND", "USA", "2020-03-01"),
        )
        # Incidences: CAN=2, IND=2, AUS=1, USA=1. Top 3 includes AUS.
        selected = select_countries(history, selection_year=2020, limit=3)
        future = tuple(event(str(100+i), "USA", "ZZZ", "2024-01-01") for i in range(20))
        self.assertEqual(selected, ("AUS", "CAN", "IND"))
        self.assertEqual(select_countries(history+future, 2020, 3), selected)

    def test_four_countries_produce_all_six_pairs_including_unseen(self):
        self.assertEqual(candidate_pairs(tuple(reversed(COUNTRIES))), (
            ("AUS","CAN"), ("AUS","IND"), ("AUS","USA"),
            ("CAN","IND"), ("CAN","USA"), ("IND","USA"),
        ))

    def test_duplicate_roster_entry_is_rejected(self):
        with self.assertRaises(DataContractError):
            candidate_pairs(("AUS", "CAN", "AUS"))

    def test_every_model_must_score_exactly_same_candidate_keys(self):
        pairs = (("AUS", "CAN"), ("AUS", "IND"), ("CAN", "IND"))
        self.assertIsNone(validate_prediction_keys({"persistence":pairs, "timestral":pairs[::-1]}, pairs))
        with self.assertRaises(DataContractError):
            validate_prediction_keys({"persistence":pairs, "timestral":pairs[:-1]}, pairs)

    def test_duplicate_prediction_key_cannot_hide_missing_pair(self):
        pairs = (("AUS", "CAN"), ("AUS", "IND"), ("CAN", "IND"))
        with self.assertRaises(DataContractError):
            validate_prediction_keys({"arima":(pairs[0],pairs[0],pairs[2])}, pairs)

