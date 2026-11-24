from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache
import math

from .artifacts import digest
from .graph import pair_graph_features, rolling_graph
from .ingestion import deduplicate_events
from .temporal import date_window, require_coverage
from .universe import candidate_pairs


@dataclass(frozen=True)
class History:
    origin: object
    origins_days: tuple
    pairs: tuple
    counts: object
    covariates: object
    topology: object
    recent: object
    hash: str


class FeaturePanel:
    def __init__(self, events, countries, complete_days, context=90, width=30, horizon=30):
        self.pairs = candidate_pairs(countries)
        self.countries = tuple(sorted(countries))
        self.complete = set(complete_days)
        self.context = context
        self.width = width
        self.horizon = horizon
        self.daily = defaultdict(Counter)
        self.events = defaultdict(list)
        cohort = set(countries)
        for event in deduplicate_events(events):
            if set(event.pair) <= cohort:
                self.daily[event.observed_day][event.pair] += 1
                self.events[event.observed_day].append(event)
        self.snapshot = lru_cache(maxsize=None)(self.snapshot)

    def snapshot(self, day):
        support = date_window(day, self.width)
        graph = rolling_graph((e for d in support for e in self.events.get(d, ())),
                              day, self.countries, self.complete, self.width)
        return [(f.jaccard, f.common_neighbors, f.preferential_attachment,
                 min(len(graph[a]), len(graph[b])), max(len(graph[a]), len(graph[b])))
                for a, b in self.pairs for f in (pair_graph_features(graph, (a, b)),)]

    def history(self, origin):
        import numpy as np

        days = date_window(origin, self.context)
        require_coverage(date_window(origin, self.context + self.width - 1), self.complete)
        counts = np.array([[self.daily.get(day, {}).get(pair, 0) for day in days]
                           for pair in self.pairs], dtype=np.int64)
        graphs = np.array([self.snapshot(day) for day in days]).transpose(1, 0, 2)
        topology = graphs[:, -1, :].copy()
        topology[:, 2] = [math.log1p(value) for value in topology[:, 2]]
        covariates = graphs[:, :, [0, 2]]
        signature = digest([str(origin), self.context, self.width, self.pairs, counts.tolist(), graphs.tolist()])
        return History(origin, days, self.pairs, counts, covariates, topology,
                       counts[:, -self.width:].sum(axis=1), signature)

    def future_counts(self, origin):
        import numpy as np

        days = date_window(origin + timedelta(days=self.horizon), self.horizon)
        require_coverage(days, self.complete)
        return np.array([sum(self.daily.get(day, {}).get(pair, 0) for day in days)
                         for pair in self.pairs])

    def labels(self, origin):
        return (self.future_counts(origin) > 0).astype(int)
