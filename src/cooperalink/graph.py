"""Daily trailing-window graph contracts."""

from collections.abc import Collection, Iterable, Mapping
from datetime import date

from .domain import DataContractError, Event, Graph, GraphFeatures, Pair
from .temporal import date_window, require_coverage


def rolling_graph(
    events: Iterable[Event],
    as_of: date,
    countries: Collection[str],
    complete_days: Collection[date],
    window_days: int = 30,
) -> Graph:
    """Simple undirected graph on the fixed cohort from [as_of-window+1,as_of].

    Keep isolated roster nodes. Exclude out-of-cohort endpoints and future rows.
    Multiplicity does not change adjacency. Require full window coverage.
    """
    days = set(date_window(as_of, window_days))
    require_coverage(days, complete_days)
    graph = {country: set() for country in countries}
    for event in events:
        a, b = event.pair
        if a != b and a in graph and b in graph and event.observed_day in days:
            graph[a].add(b)
            graph[b].add(a)
    return {country: frozenset(neighbors) for country, neighbors in graph.items()}


def pair_graph_features(
    graph: Mapping[str, Collection[str]], pair: Pair
) -> GraphFeatures:
    """Standard open-neighbor CN/Jaccard/degree-product on the full graph.

    Jaccard is zero if union is empty. Do not remove an existing pair edge before
    calculating historical features. Pair endpoints must exist in the graph.
    """
    if any(code not in graph for code in pair):
        raise DataContractError(f"Unknown graph endpoints: {pair}")
    a, b = (set(graph[code]) for code in pair)
    common = len(a & b)
    union = len(a | b)
    return GraphFeatures(common, common / union if union else 0.0, len(a) * len(b))

