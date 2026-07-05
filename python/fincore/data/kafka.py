"""Optional Kafka sink for fincore data streams."""

from __future__ import annotations

from collections.abc import AsyncIterable
import json
from typing import Any


class KafkaSink:
    """Publish normalized fincore stream events to Kafka.

    ``aiokafka`` is imported lazily so Kafka remains an optional dependency.

    :param bootstrap_servers: Kafka bootstrap server string.
    :type bootstrap_servers: str
    :param topic: Kafka topic to publish to.
    :type topic: str
    :param producer_kwargs: Additional keyword arguments passed to ``AIOKafkaProducer``.
    :type producer_kwargs: Any
    """

    def __init__(self, bootstrap_servers: str, topic: str, **producer_kwargs: Any) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer_kwargs = producer_kwargs

    async def publish_stream(self, events: AsyncIterable[dict[str, Any]]) -> int:
        """Publish every event from an async stream to Kafka.

        :param events: Async iterable of event envelopes.
        :type events: AsyncIterable[dict[str, Any]]
        :returns: Number of published events.
        :rtype: int
        :raises RuntimeError: If ``aiokafka`` is not installed.
        """

        producer = await self._start_producer()
        count = 0
        try:
            async for event in events:
                key = str(event.get("symbol", "")).encode("utf-8") or None
                value = json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
                await producer.send_and_wait(self.topic, value=value, key=key)
                count += 1
        finally:
            await producer.stop()

        return count

    async def publish_event(self, event: dict[str, Any]) -> None:
        """Publish one event envelope to Kafka.

        :param event: Event envelope.
        :type event: dict[str, Any]
        :returns: None.
        :rtype: None
        :raises RuntimeError: If ``aiokafka`` is not installed.
        """

        producer = await self._start_producer()
        try:
            key = str(event.get("symbol", "")).encode("utf-8") or None
            value = json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
            await producer.send_and_wait(self.topic, value=value, key=key)
        finally:
            await producer.stop()

    async def _start_producer(self) -> Any:
        try:
            from aiokafka import AIOKafkaProducer
        except ImportError as exc:
            raise RuntimeError("Kafka support requires installing fincore-py[kafka]") from exc

        producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            **self.producer_kwargs,
        )
        await producer.start()
        return producer
