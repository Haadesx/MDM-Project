"""Tie-aware scientific ranking metrics."""

from collections import defaultdict
from collections.abc import Collection, Sequence
from itertools import combinations, groupby
from math import fsum, isfinite
from numbers import Real
from operator import attrgetter

from .domain import DataContractError, Metric, MRRResult, PrecisionAtK, Prediction


def _validated(predictions):
    seen = set()
    for row in predictions:
        if (
            not isinstance(row.pair, tuple)
            or len(row.pair) != 2
            or any(not isinstance(code, str) or not code for code in row.pair)
            or row.pair[0] >= row.pair[1]
            or row.pair in seen
        ):
            raise DataContractError(f"Invalid or duplicate prediction pair {row.pair!r}")
        if not isinstance(row.score, Real) or not isfinite(row.score) or row.label not in (0, 1):
            raise DataContractError(f"Invalid prediction score or label for {row.pair}")
        seen.add(row.pair)
    return seen


def _score_blocks(predictions):
    _validated(predictions)
    score = attrgetter("score")
    for _, block in groupby(sorted(predictions, key=score, reverse=True), key=score):
        labels = [row.label for row in block]
        yield len(labels), sum(labels)


def roc_auc(predictions: Sequence[Prediction]) -> Metric:
    """Pairwise ROC AUC with half credit for tied positive/negative scores.

    Return None with a nonempty reason if either label class is absent. Reject
    nonfinite scores, labels outside {0,1}, and duplicate pair keys.
    """
    blocks = list(_score_blocks(predictions))
    positives = sum(positive for _, positive in blocks)
    negatives = len(predictions) - positives
    if not positives or not negatives:
        return Metric(None, "no_positives" if not positives else "no_negatives")

    negatives_below = negatives
    wins = 0.0
    for size, positive in blocks:
        negative = size - positive
        negatives_below -= negative
        wins += positive * (negatives_below + negative / 2)
    return Metric(wins / (positives * negatives))


def average_precision(predictions: Sequence[Prediction]) -> Metric:
    """Threshold-based AP; equal scores form a single threshold block.

    This is the step-wise average-precision definition, not trapezoidal PR area.
    No positives => None+reason; all positives => 1. Reject invalid predictions.
    """
    blocks = list(_score_blocks(predictions))
    positives = sum(positive for _, positive in blocks)
    if not positives:
        return Metric(None, "no_positives")

    retrieved = retrieved_positives = 0
    weighted_precision = []
    for size, positive in blocks:
        retrieved += size
        retrieved_positives += positive
        weighted_precision.append(positive * retrieved_positives / retrieved)
    return Metric(fsum(weighted_precision) / positives)


def precision_at_k(
    predictions: Sequence[Prediction], k: int
) -> PrecisionAtK:
    """Expected precision with uniform ordering inside an exact-score tie block.

    k_effective=min(k,n). If the cutoff intersects a tied block of size m holding
    p positives with r positions remaining, that block contributes r*p/m hits.
    All-negative nonempty input yields 0. k<=0 is invalid; empty input yields
    value=None, effective_k=0, expected_hits=0. Lexical ties are display-only.
    """
    if type(k) is not int or k <= 0:
        raise DataContractError("Precision@K requires a positive integer K")
    effective = min(k, len(predictions))
    if not effective:
        return PrecisionAtK(None, k, 0, 0.0)
    remaining = effective
    hits = 0.0
    for size, positive in _score_blocks(predictions):
        selected = min(remaining, size)
        hits += selected * positive / size
        remaining -= selected
        if not remaining:
            break
    return PrecisionAtK(hits / effective, k, effective, hits)


def filtered_mrr(
    predictions: Sequence[Prediction], countries: Collection[str]
) -> MRRResult:
    """Filtered endpoint-query MRR with mean ranks inside exact-score ties.

    Every positive undirected edge contributes two directed queries (u->v,v->u).
    For each query remove OTHER positive counterparts of that focal country,
    keep the target and all negatives, then target rank = 1 + higher + tied/2,
    where tied counts OTHER remaining candidates with the same score. Mean the
    reciprocals across directed positive queries. No positives => None+reason.
    Require the complete candidate-pair table for the supplied country cohort.
    """
    keys = _validated(predictions)
    if len(set(countries)) != len(countries) or keys != set(combinations(sorted(countries), 2)):
        raise DataContractError("Filtered MRR requires the complete canonical pair table")

    negatives_by_country = defaultdict(list)
    for row in predictions:
        if not row.label:
            for country in row.pair:
                negatives_by_country[country].append(row.score)

    reciprocal_ranks = []
    for row in predictions:
        if row.label:
            for country in row.pair:
                negatives = negatives_by_country[country]
                higher = sum(score > row.score for score in negatives)
                tied = sum(score == row.score for score in negatives)
                reciprocal_ranks.append(1 / (1 + higher + tied / 2))
    queries = len(reciprocal_ranks)
    if not queries:
        return MRRResult(None, 0, "no_positives")
    return MRRResult(fsum(reciprocal_ranks) / queries, queries)

