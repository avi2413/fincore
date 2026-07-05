"""Compute metrics from external database-style rows."""

from __future__ import annotations

from fincore.analytics import MetricEngine, MetricSpec


def main() -> None:
    db_rows = [
        {"ticker": "aapl", "ts": "2024-01-01T00:00:00+00:00", "close_price": 100.0, "share_volume": 1000},
        {"ticker": "aapl", "ts": "2024-01-02T00:00:00+00:00", "close_price": 104.0, "share_volume": 1100},
        {"ticker": "aapl", "ts": "2024-01-03T00:00:00+00:00", "close_price": 102.0, "share_volume": 1200},
        {"ticker": "aapl", "ts": "2024-01-04T00:00:00+00:00", "close_price": 108.0, "share_volume": 1300},
    ]

    engine = MetricEngine()
    events = engine.compute(
        db_rows,
        metrics=[
            "return.simple",
            MetricSpec("momentum.acceleration"),
            MetricSpec("auc.window", window=3),
        ],
        field_map={
            "symbol": "ticker",
            "event_time": "ts",
            "close": "close_price",
            "volume": "share_volume",
        },
    )

    for event in events:
        print(event)


if __name__ == "__main__":
    main()
