"""Utility helpers for date normalization and instrument fuzzy matching."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from difflib import SequenceMatcher
import re
from typing import Any

_STOP_WORDS = {
    "class",
    "common",
    "com",
    "corp",
    "corporation",
    "etf",
    "inc",
    "incorporated",
    "ltd",
    "plc",
    "shares",
    "stock",
    "the",
    "trust",
}

SUPPORTED_INTERVALS = {
    "1m",
    "2m",
    "5m",
    "15m",
    "30m",
    "60m",
    "90m",
    "1h",
    "1d",
    "5d",
    "1wk",
    "1mo",
    "3mo",
}

_INTERVAL_ALIASES = {
    "1min": "1m",
    "1minute": "1m",
    "2min": "2m",
    "5min": "5m",
    "15min": "15m",
    "30min": "30m",
    "60min": "60m",
    "1hr": "1h",
    "1hour": "1h",
    "hour": "1h",
    "daily": "1d",
    "day": "1d",
    "weekly": "1wk",
    "week": "1wk",
    "monthly": "1mo",
    "month": "1mo",
}

_INTRADAY_LIMIT_DAYS = {
    "1m": 7,
    "2m": 60,
    "5m": 60,
    "15m": 60,
    "30m": 60,
    "60m": 730,
    "90m": 60,
    "1h": 730,
}


def coerce_date(value: Any) -> str:
    """Normalize common date inputs into ISO ``YYYY-MM-DD`` text.

    :param value: Date-like value supplied by the Python user.
    :type value: Any
    :returns: ISO date string in ``YYYY-MM-DD`` format.
    :rtype: str
    :raises ValueError: If the value cannot be interpreted as a date.
    """

    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass

    raise ValueError(f"invalid date {value!r}; use YYYY-MM-DD or a datetime.date")


def coerce_datetime(value: Any, *, end_of_day: bool = False) -> datetime:
    """Normalize common date/datetime inputs into UTC datetimes.

    :param value: Date-like or datetime-like value.
    :type value: Any
    :param end_of_day: Whether date-only inputs should map to 23:59:59.
    :type end_of_day: bool
    :returns: Timezone-aware UTC datetime.
    :rtype: datetime
    :raises ValueError: If the value cannot be interpreted as a date or datetime.
    """

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.max if end_of_day else time.min)
    else:
        text = str(value).strip()
        parsed = None
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d",
            "%Y%m%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%m-%d-%Y",
        ):
            try:
                parsed = datetime.strptime(text, fmt)
                if fmt in {"%Y-%m-%d", "%Y%m%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"}:
                    parsed = datetime.combine(parsed.date(), time.max if end_of_day else time.min)
                break
            except ValueError:
                pass

        if parsed is None:
            try:
                parsed = datetime.fromisoformat(text)
            except ValueError as exc:
                raise ValueError(f"invalid datetime {value!r}; use YYYY-MM-DD or YYYY-MM-DD HH:MM") from exc

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_interval(interval: str) -> str:
    """Normalize a user interval into Yahoo Finance's chart interval values.

    :param interval: User interval such as ``"5m"``, ``"1hour"``, or ``"day"``.
    :type interval: str
    :returns: Yahoo-compatible interval.
    :rtype: str
    :raises ValueError: If the interval is unsupported.
    """

    normalized = str(interval).strip().lower().replace(" ", "")
    normalized = _INTERVAL_ALIASES.get(normalized, normalized)
    if normalized not in SUPPORTED_INTERVALS:
        supported = ", ".join(sorted(SUPPORTED_INTERVALS))
        raise ValueError(f"unsupported interval {interval!r}; supported intervals: {supported}")
    return normalized


def coerce_yahoo_period(start: Any, end: Any, interval: str) -> tuple[int, int, str]:
    """Normalize a user range into Yahoo period timestamps and interval.

    :param start: Inclusive range start.
    :type start: Any
    :param end: Inclusive range end.
    :type end: Any
    :param interval: User interval.
    :type interval: str
    :returns: ``period1``, ``period2``, and normalized interval.
    :rtype: tuple[int, int, str]
    :raises ValueError: If the range or interval is invalid.
    """

    normalized_interval = normalize_interval(interval)
    start_dt = coerce_datetime(start)
    end_dt = coerce_datetime(end, end_of_day=True)

    if end_dt <= start_dt:
        raise ValueError("end must be after start")

    validate_interval_range(start_dt, end_dt, normalized_interval)
    return int(start_dt.timestamp()), int(end_dt.timestamp()), normalized_interval


def validate_interval_range(start: datetime, end: datetime, interval: str) -> None:
    """Validate Yahoo's approximate retention limits for intraday intervals.

    :param start: UTC start datetime.
    :type start: datetime
    :param end: UTC end datetime.
    :type end: datetime
    :param interval: Normalized Yahoo interval.
    :type interval: str
    :returns: None.
    :rtype: None
    :raises ValueError: If the requested range is too large for the interval.
    """

    max_days = _INTRADAY_LIMIT_DAYS.get(interval)
    if max_days is None:
        return

    requested_days = (end - start).total_seconds() / 86_400
    if requested_days > max_days:
        raise ValueError(
            f"Yahoo interval {interval!r} supports roughly {max_days} days of history; "
            f"requested {requested_days:.1f} days."
        )


def lookback_start(lookback: str, *, end: datetime | None = None) -> datetime:
    """Calculate a UTC start datetime from a compact lookback expression.

    :param lookback: Expression such as ``"1d"``, ``"6h"``, or ``"30m"``.
    :type lookback: str
    :param end: Optional UTC end datetime. Defaults to now.
    :type end: datetime | None
    :returns: Start datetime.
    :rtype: datetime
    """

    end = end or datetime.now(timezone.utc)
    text = lookback.strip().lower()
    match = re.fullmatch(r"(\d+)(m|h|d|w)", text)
    if not match:
        raise ValueError("lookback must look like '30m', '6h', '1d', or '2w'")

    amount = int(match.group(1))
    unit = match.group(2)
    delta = {
        "m": timedelta(minutes=amount),
        "h": timedelta(hours=amount),
        "d": timedelta(days=amount),
        "w": timedelta(weeks=amount),
    }[unit]
    return end - delta


def normalize_search_text(value: str) -> str:
    """Normalize a symbol or instrument name for fuzzy matching.

    :param value: Raw user query or instrument field.
    :type value: str
    :returns: Lowercase token string with noisy finance/legal words removed.
    :rtype: str
    """

    text = value.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if token and token not in _STOP_WORDS]
    return " ".join(tokens)


def score_instrument(query: str, instrument: dict[str, Any]) -> tuple[float, str]:
    """Score an instrument against a normalized human query.

    :param query: Normalized user query from :func:`normalize_search_text`.
    :type query: str
    :param instrument: Instrument dictionary returned by the Rust core.
    :type instrument: dict[str, Any]
    :returns: Match score and reason.
    :rtype: tuple[float, str]
    """

    symbol = normalize_search_text(instrument["symbol"])
    name = normalize_search_text(instrument["name"])
    maturity = normalize_search_text(str(instrument.get("maturity", "")))

    if query == symbol:
        return 1.0, "exact_symbol"
    if query == name:
        return 0.99, "exact_name"
    if maturity and query == maturity:
        return 0.98, "exact_maturity"

    candidates = [
        (symbol, "symbol"),
        (name, "name"),
        (f"{symbol} {name}".strip(), "symbol_name"),
        (maturity, "maturity"),
    ]

    best_score = 0.0
    best_reason = "no_match"
    for candidate, reason in candidates:
        if not candidate:
            continue
        score = SequenceMatcher(None, query, candidate).ratio()
        if query in candidate:
            score = max(score, 0.82 if reason != "symbol" else 0.9)
        if candidate in query:
            score = max(score, 0.78)

        if score > best_score:
            best_score = score
            best_reason = f"fuzzy_{reason}"

    return best_score, best_reason
