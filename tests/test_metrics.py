import unittest
from dataclasses import replace

from cooperalink.domain import DataContractError, Prediction
from cooperalink.metrics import average_precision, filtered_mrr, precision_at_k, roc_auc
from tests.helpers import ranking_fixture

RANK_COUNTRIES = ("A", "B", "C", "D")


class MetricContractTests(unittest.TestCase):
    def test_auc_gives_half_credit_to_ties(self):
        # AB positive .7 wins against BC,BD,CD, ties AC, loses AD: 3.5/5.
        self.assertAlmostEqual(roc_auc(ranking_fixture()).value,0.7)

    def test_ap_uses_threshold_tie_blocks_not_a_lexical_rank(self):
        # At the .7 threshold all three AD,AB,AC are retrieved; one is positive.
        self.assertAlmostEqual(average_precision(ranking_fixture()).value,1/3)

    def test_precision_at_k_uses_expected_cutoff_tie_hits(self):
        result = precision_at_k(ranking_fixture(),2)
        self.assertEqual(result.effective_k,2)
        self.assertAlmostEqual(result.expected_hits,0.5)
        self.assertAlmostEqual(result.value,0.25)
        self.assertEqual(result,precision_at_k(tuple(reversed(ranking_fixture())),2))

    def test_precision_caps_k_to_available_candidates(self):
        result = precision_at_k(ranking_fixture(),100)
        self.assertEqual(result.requested_k,100)
        self.assertEqual(result.effective_k,6)
        self.assertAlmostEqual(result.value,1/6)

    def test_filtered_mrr_uses_mean_tie_rank_for_each_positive_endpoint(self):
        # A->B: AD is higher, AC is tied -> rank2.5, RR.4; B->A: rank1, RR1.
        result = filtered_mrr(ranking_fixture(),RANK_COUNTRIES)
        self.assertEqual(result.positive_query_count,2)
        self.assertAlmostEqual(result.value,0.7)

    def test_filtered_mrr_removes_other_true_counterparts(self):
        rows = (Prediction(("A","B"),0.8,1),Prediction(("A","C"),0.9,1),
                Prediction(("B","C"),0.1,0))
        # For A->B, AC is another positive and is filtered. All four queries rank1.
        result = filtered_mrr(rows,("A","B","C"))
        self.assertEqual(result.positive_query_count,4)
        self.assertEqual(result.value,1.0)

    def test_one_class_metrics_are_explicit_and_no_positive_is_not_success(self):
        negatives = tuple(replace(p,label=0) for p in ranking_fixture())
        positives = tuple(replace(p,label=1) for p in ranking_fixture())
        self.assertIsNone(roc_auc(negatives).value)
        self.assertTrue(roc_auc(negatives).reason)
        self.assertIsNone(roc_auc(positives).value)
        self.assertIsNone(average_precision(negatives).value)
        self.assertTrue(average_precision(negatives).reason)
        self.assertEqual(average_precision(positives).value,1.0)
        self.assertIsNone(filtered_mrr(negatives,RANK_COUNTRIES).value)
        self.assertEqual(filtered_mrr(negatives,RANK_COUNTRIES).positive_query_count,0)
        self.assertEqual(precision_at_k(negatives,2).value,0.0)

    def test_nonfinite_scores_and_incomplete_mrr_tables_are_rejected(self):
        invalid = (replace(ranking_fixture()[0],score=float("nan")),)+ranking_fixture()[1:]
        with self.assertRaises(DataContractError):
            roc_auc(invalid)
        with self.assertRaises(DataContractError):
            filtered_mrr(ranking_fixture()[:-1],RANK_COUNTRIES)

