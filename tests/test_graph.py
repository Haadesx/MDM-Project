import unittest
from datetime import date, timedelta

from cooperalink.domain import CoverageError, GraphFeatures
from cooperalink.graph import pair_graph_features, rolling_graph
from tests.helpers import COUNTRIES, ORIGIN, complete_days, event, fixture_events


class GraphContractTests(unittest.TestCase):
    def test_graph_uses_trailing_30_days_and_keeps_fixed_nodes(self):
        graph = rolling_graph(fixture_events(),ORIGIN,COUNTRIES,complete_days())
        self.assertEqual(graph, {
            "AUS":frozenset({"CAN"}), "CAN":frozenset({"AUS","IND"}),
            "IND":frozenset({"CAN","USA"}), "USA":frozenset({"IND"}),
        })

    def test_pair_features_match_hand_calculated_path_graph(self):
        graph = {"AUS":{"CAN"}, "CAN":{"AUS","IND"}, "IND":{"CAN","USA"}, "USA":{"IND"}}
        self.assertEqual(pair_graph_features(graph,("AUS","IND")),GraphFeatures(1,0.5,2))
        self.assertEqual(pair_graph_features(graph,("CAN","IND")),GraphFeatures(0,0.0,4))

    def test_isolated_nodes_have_zero_features(self):
        graph = {"AUS":set(),"CAN":set()}
        self.assertEqual(pair_graph_features(graph,("AUS","CAN")),GraphFeatures(0,0.0,0))

    def test_future_rows_cannot_change_historical_topology(self):
        base = tuple(e for e in fixture_events() if e.observed_day <= ORIGIN)
        future = base + (event("999","AUS","USA","2024-02-01"),)
        self.assertEqual(rolling_graph(base,ORIGIN,COUNTRIES,complete_days()),
                         rolling_graph(future,ORIGIN,COUNTRIES,complete_days()))

    def test_graph_includes_lower_boundary_without_a_later_record(self):
        # The main fixture also has a Jan 31 record for this pair; isolate Jan 2.
        lower_only = (event("boundary", "AUS", "CAN", "2024-01-02"),)
        graph = rolling_graph(lower_only,ORIGIN,COUNTRIES,complete_days())
        self.assertEqual(graph["AUS"],frozenset({"CAN"}))
        self.assertEqual(graph["CAN"],frozenset({"AUS"}))
        self.assertEqual(graph["IND"],frozenset())
        self.assertEqual(graph["USA"],frozenset())

    def test_earliest_context_graph_requires_119_raw_days(self):
        context_start = ORIGIN - timedelta(days=89)
        raw_start = ORIGIN - timedelta(days=118)
        cov = frozenset(raw_start+timedelta(days=i) for i in range(119))
        self.assertEqual(raw_start,date(2023,10,5))
        with self.assertRaises(CoverageError):
            rolling_graph((),context_start,COUNTRIES,cov-{raw_start})
        graph = rolling_graph((),context_start,COUNTRIES,cov)
        self.assertEqual(set(graph),set(COUNTRIES))
        self.assertTrue(all(not neighbors for neighbors in graph.values()))

