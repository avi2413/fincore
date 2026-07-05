"""Tests for stream event envelopes."""

from __future__ import annotations

from fincore.data import bar_event, bond_yield_event


def test_bar_event_shape() -> None:
    event = bar_event(
        {
            "source": "yahoo",
            "symbol": "AAPL",
            "interval": "5m",
            "event_time": "2024-01-02T14:30:00+00:00",
            "date": "2024-01-02",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 123456.0,
            "received_time": "2024-01-02T14:31:00+00:00",
            "raw": "{}",
        },
        stream_type="historical_replay",
    )

    assert event["event_type"] == "bar"
    assert event["stream_type"] == "historical_replay"
    assert event["source"] == "yahoo"
    assert event["symbol"] == "AAPL"
    assert event["payload"]["timeframe"] == "5m"
    assert event["payload"]["close"] == 100.5


def test_bond_yield_event_shape() -> None:
    event = bond_yield_event(
        {
            "source": "fred",
            "series_id": "DGS10",
            "date": "2024-01-02",
            "value": 4.0,
            "received_time": "2024-01-02T00:00:00+00:00",
            "raw": "2024-01-02,4.0",
        },
        stream_type="historical_replay",
    )

    assert event["event_type"] == "bond_yield"
    assert event["symbol"] == "DGS10"
    assert event["event_time"] == "2024-01-02"
    assert event["payload"] == {"value": 4.0}
