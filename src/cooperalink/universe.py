"""Training-only country roster and all-pairs prediction coverage contracts."""

from collections.abc import Iterable, Mapping, Sequence

from collections import Counter
from itertools import combinations

from .domain import DataContractError, Event, Pair
from .ingestion import deduplicate_events


def select_countries(
    events: Iterable[Event], selection_year: int = 2020, limit: int = 30
) -> tuple[str, ...]:
    """Select by distinct-ID endpoint incidence in selection_year only.

    Use Event.observed_day. Sort candidates by descending incidence then code,
    select at most limit, and return selected country codes in lexical order.
    No event from later years may affect selection. limit must be positive.
    """
    if limit < 1:
        raise DataContractError("Country limit must be positive")
    incidence = country_incidence(events, selection_year)
    return tuple(sorted(list(incidence)[:limit]))


def country_incidence(events, year):
    counts = Counter(code for event in deduplicate_events(
        event for event in events if event.observed_day.year == year
    ) for code in event.pair)
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def candidate_pairs(countries: Sequence[str]) -> tuple[Pair, ...]:
    """All lexically ordered, unique, unordered pairs; no observed-link filter.

    Reject duplicate country entries rather than silently changing the roster.
    """
    if len(countries) != len(set(countries)):
        raise DataContractError("Duplicate country roster entries")
    return tuple(combinations(sorted(countries), 2))


def validate_prediction_keys(
    by_model: Mapping[str, Sequence[Pair]], expected_pairs: Sequence[Pair]
) -> None:
    """For one origin, each model must predict every expected pair exactly once.

    Missing, duplicate, extra or noncanonical keys raise DataContractError.
    This checks only keys; unavailable models must have explicit run statuses.
    """
    expected = set(expected_pairs)
    for model, pairs in by_model.items():
        if len(pairs) != len(expected) or set(pairs) != expected:
            raise DataContractError(f"{model} does not score every expected pair exactly once")

