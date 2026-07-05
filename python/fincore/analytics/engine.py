"""Metric engine for batch and streaming market analytics."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Mapping
from typing import Any

from fincore import _fincore

from .models import MetricSpec
from .normalize import normalize_bar

DEFAULT_METRICS = (
    MetricSpec("return.simple"),
    MetricSpec("return.log"),
    MetricSpec("momentum.roc", window=3),
    MetricSpec("momentum.derivative"),
    MetricSpec("momentum.acceleration"),
    MetricSpec("volatility.rolling", window=5),
    MetricSpec("drawdown.current"),
    MetricSpec("auc.window", window=5),
)


class MetricEngine:
    """Compute normalized metric events from bars or bar stream events."""

    def __init__(
        self,
        metrics: Iterable[str | dict[str, Any] | MetricSpec] | None = None,
        *,
        max_window: int | None = None,
        field_map: Mapping[str, str] | None = None,
    ) -> None:
        """Create a metric engine.

        :param metrics: Default metrics used by ``compute`` and ``update``.
        :type metrics: Iterable[str | dict[str, Any] | MetricSpec] | None
        :param max_window: Optional streaming buffer size override.
        :type max_window: int | None
        :param field_map: Optional external-source field map.
        :type field_map: Mapping[str, str] | None
        """

        self.metrics = self._normalize_specs(metrics or DEFAULT_METRICS)
        self.field_map = dict(field_map or {})
        largest_window = max((spec.window for spec in self.metrics), default=1)
        self.max_window = max_window or max(largest_window + 2, 3)
        self._buffers: dict[str, deque[dict[str, Any]]] = defaultdict(
            lambda: deque(maxlen=self.max_window)
        )
        self._emitted: set[tuple[str, str, str]] = set()

    def compute(
        self,
        records: Iterable[Mapping[str, Any]],
        metrics: Iterable[str | dict[str, Any] | MetricSpec] | None = None,
        *,
        field_map: Mapping[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Compute metric events for a finite batch of records.

        :param records: Bar rows, stream envelopes, or external source mappings.
        :type records: Iterable[Mapping[str, Any]]
        :param metrics: Optional metric override.
        :type metrics: Iterable[str | dict[str, Any] | MetricSpec] | None
        :param field_map: Optional external-source field map override.
        :type field_map: Mapping[str, str] | None
        :returns: Normalized metric events.
        :rtype: list[dict[str, Any]]
        """

        mapping = {**self.field_map, **(field_map or {})}
        bars = [normalize_bar(record, field_map=mapping) for record in records]
        specs = self._normalize_specs(metrics) if metrics is not None else self.metrics
        return _fincore.compute_bar_metrics(bars, [spec.to_rust() for spec in specs])

    def update(
        self,
        record: Mapping[str, Any],
        metrics: Iterable[str | dict[str, Any] | MetricSpec] | None = None,
        *,
        field_map: Mapping[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Update streaming state with one record and emit newly available metrics.

        :param record: Bar row or bar stream envelope.
        :type record: Mapping[str, Any]
        :param metrics: Optional metric override.
        :type metrics: Iterable[str | dict[str, Any] | MetricSpec] | None
        :param field_map: Optional external-source field map override.
        :type field_map: Mapping[str, str] | None
        :returns: New metric events for this update.
        :rtype: list[dict[str, Any]]
        """

        mapping = {**self.field_map, **(field_map or {})}
        bar = normalize_bar(record, field_map=mapping)
        buffer = self._buffers[bar["symbol"]]
        buffer.append(bar)

        emitted = []
        for event in self.compute(buffer, metrics=metrics):
            key = (event["metric"], event["symbol"], event["event_time"])
            if key in self._emitted:
                continue
            self._emitted.add(key)
            emitted.append(event)
        return emitted

    async def run(
        self,
        records: Any,
        metrics: Iterable[str | dict[str, Any] | MetricSpec] | None = None,
    ) -> Any:
        """Yield metric events from an async stream of market records.

        :param records: Async iterable of bar rows or stream envelopes.
        :type records: Any
        :param metrics: Optional metric override.
        :type metrics: Iterable[str | dict[str, Any] | MetricSpec] | None
        :yields: Metric event dictionaries.
        :rtype: AsyncIterator[dict[str, Any]]
        """

        async for record in records:
            for event in self.update(record, metrics=metrics):
                yield event

    @staticmethod
    def _normalize_specs(
        metrics: Iterable[str | dict[str, Any] | MetricSpec] | None,
    ) -> list[MetricSpec]:
        return [MetricSpec.from_value(metric) for metric in (metrics or ())]
