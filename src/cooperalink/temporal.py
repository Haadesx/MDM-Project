"""Calendar, counts, outcome, persistence and chronology contracts."""

from collections.abc import Collection, Iterable, Sequence
from collections import Counter
from datetime import date, timedelta

from .domain import CoverageError, Event, Fold, LeakageError, Pair
from .ingestion import deduplicate_events


def date_window(end: date, length: int) -> tuple[date, ...]:
    """Exactly length daily dates, increasing and inclusive of end; length > 0."""
    if length <= 0:
        raise ValueError("Window length must be positive")
    return tuple(end - timedelta(days=offset) for offset in range(length - 1, -1, -1))


def require_coverage(days, complete_days):
    missing = sorted(set(days).difference(complete_days))
    if missing:
        raise CoverageError(f"Uncertified coverage on {missing[0]} ({len(missing)} missing days)")


def daily_counts(
    events: Iterable[Event],
    pair: Pair,
    days: Sequence[date],
    complete_days: Collection[date],
) -> tuple[int, ...]:
    """Count distinct IDs per DATEADDED UTC day for a canonical pair.

    Output aligns exactly with days; complete empty days become zero. A missing
    complete-day certificate raises CoverageError, including on zero-event days.
    Duplicate IDs are idempotent; conflicting identities raise DataContractError.
    """
    require_coverage(days, complete_days)
    wanted = set(days)
    counts = Counter(event.observed_day for event in deduplicate_events(
        event for event in events if event.observed_day in wanted
    ) if event.pair == pair)
    return tuple(counts[day] for day in days)


def link_label(
    events: Iterable[Event],
    pair: Pair,
    origin: date,
    complete_days: Collection[date],
    horizon: int = 30,
) -> int:
    """1 iff any distinct record has origin < observed_day <= origin+horizon.

    Every label day requires complete coverage. The origin day is excluded.
    """
    days = date_window(origin + timedelta(days=horizon), horizon)
    return int(any(daily_counts(events, pair, days, complete_days)))


def persistence(
    events: Iterable[Event],
    pair: Pair,
    origin: date,
    complete_days: Collection[date],
    lookback: int = 30,
) -> int:
    """1 iff any record occurs in [origin-lookback+1, origin], inclusive.

    No later event may affect this score. All historical days require coverage.
    """
    return int(any(daily_counts(events, pair, date_window(origin, lookback), complete_days)))


def annual_folds(year: int, horizon: int = 30) -> tuple[Fold, ...]:
    """Start labels Jan 1; stride horizon; retain full within-year horizons only.

    At horizon=30 this yields 12 folds; leftover 5/6 days are omitted. Origin is
    label_start minus one day, and label_end = origin+horizon.
    """
    if horizon <= 0:
        raise ValueError("Horizon must be positive")
    january = date(year, 1, 1)
    blocks = (date(year + 1, 1, 1) - january).days // horizon
    return tuple(Fold(year, index, january + timedelta(days=index * horizon - 1),
                      january + timedelta(days=index * horizon),
                      january + timedelta(days=(index + 1) * horizon - 1))
                 for index in range(blocks))


def assert_chronology(
    fitting_label_ends: Sequence[date], prediction_origin: date
) -> None:
    """All fitted labels must have fully matured by prediction_origin.

    A label end later than the origin raises LeakageError. Exact equality is
    allowed because prediction is made at the end of the origin's UTC day.
    """
    if any(day > prediction_origin for day in fitting_label_ends):
        raise LeakageError(f"Fitting labels exceed prediction cutoff {prediction_origin}")

