"""Normalization and record-identity contracts. Every algorithm starts RED."""

from collections.abc import Collection, Iterable, Mapping

from datetime import datetime, timezone
import re

from .domain import DataContractError, Event, Pair


def canonical_pair(country_a: str, country_b: str) -> Pair:
    """Return the lexically sorted pair; self-links/empty codes are invalid."""
    if not country_a or not country_b or country_a == country_b:
        raise DataContractError("Expected two distinct nonempty actor countries")
    return min(country_a, country_b), max(country_a, country_b)


def normalize_event(
    row: Mapping[str, object], valid_country_codes: Collection[str]
) -> Event | None:
    """Normalize one GDELT row or return None for an excluded event.

    EventCode must be a string; select exact '061', never prefix matches or an
    integer repaired to a padded code. Use Actor1CountryCode/Actor2CountryCode,
    not Geo fields. Blank/unknown/self actors and non-061 rows are excluded.
    DATEADDED is strict YYYYMMDDHHMMSS UTC. SQLDATE is strict YYYYMMDD.
    GlobalEventID, SQLDATE and DATEADDED may arrive as integers or digit strings;
    EventCode must arrive as a string. Malformed required fields raise
    DataContractError. No silent row repair or date coercion is permitted.
    """
    event, _ = classify_event(row, valid_country_codes)
    return event


def classify_event(row, valid_country_codes):
    code = row.get("EventCode")
    if not isinstance(code, str):
        raise DataContractError("EventCode must be a string")
    code = code.strip()
    if code == "61":
        raise DataContractError("EventCode 61 has lost the leading zero of the CAMEO code")
    if code != "061":
        return None, "relation"
    a, b = (str(row.get(key) or "").strip() for key in ("Actor1CountryCode", "Actor2CountryCode"))
    if not a or not b:
        return None, "blank_country"
    if a not in valid_country_codes or b not in valid_country_codes:
        return None, "unknown_country"
    if a == b:
        return None, "self_pair"

    identifiers = {decimal_field(row[key], key).lstrip("0") or "0"
                   for key in ("GLOBALEVENTID", "GlobalEventID") if key in row}
    if len(identifiers) != 1:
        raise DataContractError("Missing or conflicting GLOBALEVENTID aliases")
    occurred = parse_date(row.get("SQLDATE"), "SQLDATE", 8, "%Y%m%d").date()
    added = parse_date(row.get("DATEADDED"), "DATEADDED", 14, "%Y%m%d%H%M%S")
    low, high = canonical_pair(a, b)
    return Event(identifiers.pop(), low, high, occurred, added), "eligible"


def decimal_field(value, field):
    if type(value) not in (int, str) or not re.fullmatch("[0-9]+", str(value)):
        raise DataContractError(f"{field} must contain ASCII digits")
    return str(value)


def parse_date(value, field, length, fmt):
    digits = decimal_field(value, field)
    if len(digits) != length:
        raise DataContractError(f"{field} must contain exactly {length} digits")
    try:
        return datetime.strptime(digits, fmt).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise DataContractError(f"Invalid {field}: {digits}") from exc


def deduplicate_events(events: Iterable[Event]) -> tuple[Event, ...]:
    """Keep one identical immutable event per ID, sorted by event_id.

    Conflicting values for the same ID raise DataContractError. Distinct IDs for
    reciprocal actor records remain distinct counts, even on the same date.
    """
    by_id = {}
    for event in events:
        if by_id.setdefault(event.event_id, event) != event:
            raise DataContractError(f"Conflicting identity for event {event.event_id}")
    return tuple(by_id[key] for key in sorted(by_id))

