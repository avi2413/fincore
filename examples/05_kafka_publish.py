"""Publish fincore stream events to Kafka."""

from __future__ import annotations

import asyncio

from fincore.data import DataClient
from fincore.data.kafka import KafkaSink


async def main() -> None:
    client = DataClient()
    sink = KafkaSink(
        bootstrap_servers="localhost:9092",
        topic="fincore.market.bars",
    )

    count = await sink.publish_stream(
        client.replay_bars("Apple", "2024-01-01", "2024-01-05", interval="1d")
    )
    print(f"published {count} events")


if __name__ == "__main__":
    asyncio.run(main())
