"""Tests for the analytics public API."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from fincore import _fincore
from fincore.analytics import MetricEngine, MetricSpec, normalize_bar


def _bars() -> list[dict[str, object]]:
    return [
        {
            "symbol": "AAPL",
            "event_time": "2024-01-01T00:00:00+00:00",
            "interval": "1d",
            "close": 100.0,
            "volume": 1000,
        },
        {
            "symbol": "AAPL",
            "event_time": "2024-01-02T00:00:00+00:00",
            "interval": "1d",
            "close": 110.0,
            "volume": 1200,
        },
        {
            "symbol": "AAPL",
            "event_time": "2024-01-03T00:00:00+00:00",
            "interval": "1d",
            "close": 121.0,
            "volume": 1300,
        },
    ]


def test_metric_spec_accepts_string_and_dict() -> None:
    assert MetricSpec.from_value("return.simple").name == "return.simple"
    spec = MetricSpec.from_value({"name": "momentum.roc", "window": 3, "output_name": "roc_3"})

    assert spec.window == 3
    assert spec.to_rust()["output_name"] == "roc_3"


def test_normalize_bar_accepts_stream_event_envelope() -> None:
    normalized = normalize_bar(
        {
            "event_type": "bar",
            "source": "yahoo",
            "symbol": "aapl",
            "event_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "payload": {
                "interval": "1d",
                "close": "100.5",
                "volume": "1000",
            },
        }
    )

    assert normalized["symbol"] == "AAPL"
    assert normalized["close"] == 100.5
    assert normalized["volume"] == 1000.0
    assert normalized["event_time"] == "2024-01-01T00:00:00+00:00"


def test_normalize_bar_accepts_external_field_map() -> None:
    normalized = normalize_bar(
        {"ticker": "msft", "ts": "2024-01-01", "px_close": 10},
        field_map={"symbol": "ticker", "event_time": "ts", "close": "px_close"},
    )

    assert normalized["symbol"] == "MSFT"
    assert normalized["close"] == 10.0


def test_metric_engine_compute_returns_normalized_events() -> None:
    engine = MetricEngine(metrics=[MetricSpec("return.simple")])

    events = engine.compute(_bars())

    assert _fincore.last_metric_args[1] == [
        {
            "name": "return.simple",
            "window": 1,
            "input_field": "close",
            "output_name": "return.simple",
        }
    ]
    assert len(events) == 2
    assert events[0]["event_type"] == "metric"
    assert events[0]["metric"] == "return.simple"
    assert events[0]["symbol"] == "AAPL"
    assert events[0]["value"] == pytest.approx(0.1)


def test_metric_engine_compute_supports_custom_metric_specs() -> None:
    engine = MetricEngine()

    events = engine.compute(_bars(), metrics=[MetricSpec("auc.window", window=2, output_name="auc_2")])

    assert events[0]["metric"] == "auc_2"
    assert events[0]["unit"] == "price_bars"
    assert events[0]["value"] == pytest.approx(105.0)


def test_metric_engine_update_emits_only_new_stream_events() -> None:
    engine = MetricEngine(metrics=[MetricSpec("return.simple")])

    assert engine.update(_bars()[0]) == []
    first = engine.update(_bars()[1])
    second = engine.update(_bars()[1])

    assert len(first) == 1
    assert second == []
