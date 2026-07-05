"""Normalized stream event envelopes for downstream sinks."""

from __future__ import annotations

from typing import Any


def bar_event(bar: dict[str, Any], *, stream_type: str) -> dict[str, Any]:
    """Wrap a normalized bar row in a stream event envelope.

    :param bar: Normalized bar dictionary returned by the Rust core.
    :type bar: dict[str, Any]
    :param stream_type: Stream producer type, such as ``"historical_replay"``.
    :type stream_type: str
    :returns: Timescale/Kafka-friendly event envelope.
    :rtype: dict[str, Any]
    """

    return {
        "event_type": "bar",
        "stream_type": stream_type,
        "source": bar["source"],
        "symbol": bar["symbol"],
        "event_time": bar["event_time"],
        "received_time": bar["received_time"],
        "payload": {
            "interval": bar["interval"],
            "timeframe": bar["interval"],
            "date": bar["date"],
            "open": bar["open"],
            "high": bar["high"],
            "low": bar["low"],
            "close": bar["close"],
            "volume": bar["volume"],
        },
        "raw": bar["raw"],
    }


def bond_yield_event(observation: dict[str, Any], *, stream_type: str) -> dict[str, Any]:
    """Wrap a normalized bond-yield observation in a stream event envelope.

    :param observation: Normalized observation dictionary returned by the Rust core.
    :type observation: dict[str, Any]
    :param stream_type: Stream producer type.
    :type stream_type: str
    :returns: Timescale/Kafka-friendly event envelope.
    :rtype: dict[str, Any]
    """

    return {
        "event_type": "bond_yield",
        "stream_type": stream_type,
        "source": observation["source"],
        "symbol": observation["series_id"],
        "event_time": observation["date"],
        "received_time": observation["received_time"],
        "payload": {
            "value": observation["value"],
        },
        "raw": observation["raw"],
    }
