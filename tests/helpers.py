import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from cooperalink.domain import Event, Prediction

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
COUNTRIES = ("AUS", "CAN", "IND", "USA")
ORIGIN = date(2024, 1, 31)


def event(event_id, a, b, observed, occurrence=None):
    """Construct trusted normalized test data, independently of the parser stub."""
    day = date.fromisoformat(observed)
    return Event(
        str(event_id), a, b,
        date.fromisoformat(occurrence) if occurrence else day,
        datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc),
    )


def complete_days(start="2023-09-01", end="2024-04-01"):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    return frozenset(first + timedelta(days=i) for i in range((last-first).days+1))


def fixture_events():
    """Expected normalized forms of raw JSON, deliberately no parser dependency."""
    return (
        event("1001", "AUS", "CAN", "2024-01-02"),
        event("1002", "AUS", "CAN", "2024-01-31", "2024-01-20"),
        event("1003", "AUS", "IND", "2024-01-01"),
        event("1004", "CAN", "IND", "2024-01-31"),
        event("1005", "IND", "USA", "2024-01-15"),
        event("1006", "CAN", "USA", "2024-02-01"),
        event("1007", "AUS", "USA", "2024-03-01"),
        event("1008", "AUS", "IND", "2024-03-02"),
        event("1009", "IND", "USA", "2024-02-05", "2024-01-10"),
    )


def raw_events():
    return json.loads((FIXTURES / "gdelt_events_synthetic.json").read_text())


def ranking_fixture():
    rows = json.loads((FIXTURES / "ranking_synthetic.json").read_text())
    return tuple(Prediction(tuple(r["pair"]), r["score"], r["label"]) for r in rows)

