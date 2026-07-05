"""Compute batch analytics from historical bars."""

from __future__ import annotations

from fincore.analytics import MetricEngine, MetricSpec
from fincore.data import DataClient


def main() -> None:
    client = DataClient()
    bars = client.fetch_bars("Apple", "2024-01-01", "2024-02-15", interval="1d")

    engine = MetricEngine()
    metric_events = engine.compute(
        bars,
        metrics=[
            "return.simple",
            "return.log",
            MetricSpec("momentum.roc", window=3),
            MetricSpec("volatility.rolling", window=5),
            MetricSpec("drawdown.current"),
            MetricSpec("auc.window", window=5),
        ],
    )

    for event in metric_events[:10]:
        print(event)


if __name__ == "__main__":
    main()
