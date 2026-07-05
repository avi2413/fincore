"""Input normalization for analytics sources."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


DEFAULT_FIELD_MAP = {
    "symbol": "symbol",
    "event_time": "event_time",
    "interval": "interval",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
}


def _read(record: Mapping[str, Any], key: str, field_map: Mapping[str, str]) -> Any:
    source_key = field_map.get(key, key)
    return record.get(source_key)


def _coerce_event_time(value: Any) -> str:
    if isinstance(value, datetime):
        parsed = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    if value is None:
        raise ValueError("bar record requires event_time")
    return str(value)


def normalize_bar(
    record: Mapping[str, Any],
    *,
    field_map: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Normalize a bar row, stream event, or DB-style mapping for analytics.

    :param record: Bar dictionary, stream envelope, or external source row.
    :type record: Mapping[str, Any]
    :param field_map: Optional mapping from normalized names to source names.
    :type field_map: Mapping[str, str] | None
    :returns: Normalized bar dictionary for the Rust metric core.
    :rtype: dict[str, Any]
    :raises ValueError: If required fields are missing.
    """

    if record.get("event_type") == "bar" and isinstance(record.get("payload"), Mapping):
        payload = record["payload"]
        merged = {
            **payload,
            "symbol": record.get("symbol"),
            "event_time": record.get("event_time"),
            "source": record.get("source"),
            "received_time": record.get("received_time"),
        }
        record = merged

    mapping = {**DEFAULT_FIELD_MAP, **(field_map or {})}
    symbol = _read(record, "symbol", mapping)
    close = _read(record, "close", mapping)
    if symbol is None:
        raise ValueError("bar record requires symbol")
    if close is None:
        raise ValueError("bar record requires close")

    normalized = {
        "symbol": str(symbol).upper(),
        "event_time": _coerce_event_time(_read(record, "event_time", mapping)),
        "interval": _read(record, "interval", mapping),
        "open": _read(record, "open", mapping),
        "high": _read(record, "high", mapping),
        "low": _read(record, "low", mapping),
        "close": float(close),
        "volume": _read(record, "volume", mapping),
    }
    if normalized["volume"] is not None:
        normalized["volume"] = float(normalized["volume"])
    return normalized
