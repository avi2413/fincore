"""Replay historical bars and derive metrics on the fly."""

from __future__ import annotations

import asyncio

from fincore.analytics import MetricEngine, MetricSpec
from fincore.data import DataClient


async def main() -> None:
    client = DataClient()
    engine = MetricEngine(
        metrics=[
            "return.simple",
            MetricSpec("momentum.roc", window=3),
            MetricSpec("volatility.rolling", window=5),
        ]
    )

    async for event in client.replay_bars("Apple", "2024-01-01", "2024-01-31", interval="1d"):
        for metric_event in engine.update(event):
            print(metric_event)


if __name__ == "__main__":
    asyncio.run(main())
