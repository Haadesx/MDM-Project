"""Stable value types used by the executable scientific contracts.

These types are scaffolding, not a working research pipeline. Algorithm stubs live
in the sibling modules. The implementing agent may add vectorized internals while
preserving these small, easily audited public functions.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone

Pair = tuple[str, str]
Graph = dict[str, frozenset[str]]


class DataContractError(ValueError):
    """Input does not satisfy an explicit scientific data contract."""


class CoverageError(DataContractError):
    """A requested day is not verified complete; absence cannot become zero."""


class LeakageError(DataContractError):
    """Fit or observation timestamps exceed the permitted temporal cutoff."""


@dataclass(frozen=True)
class Event:
    event_id: str
    country_a: str
    country_b: str
    event_day: date  # SQLDATE, retained for audit; not the primary modeling day.
    added_at: datetime  # timezone-aware UTC DATEADDED.

    @property
    def pair(self) -> Pair:
        return (self.country_a, self.country_b)

    @property
    def observed_day(self) -> date:
        return self.added_at.astimezone(timezone.utc).date()


@dataclass(frozen=True)
class Fold:
    year: int
    index: int  # 0 through 11 for the pre-registered annual schedule.
    origin: date
    label_start: date
    label_end: date


@dataclass(frozen=True)
class GraphFeatures:
    common_neighbors: int
    jaccard: float
    preferential_attachment: int


@dataclass(frozen=True)
class Prediction:
    pair: Pair
    score: float
    label: int


@dataclass(frozen=True)
class Metric:
    value: float | None
    reason: str | None = None


@dataclass(frozen=True)
class PrecisionAtK:
    value: float | None
    requested_k: int
    effective_k: int
    expected_hits: float


@dataclass(frozen=True)
class MRRResult:
    value: float | None
    positive_query_count: int
    reason: str | None = None

