"""Analytics configuration models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MetricSpec:
    """Describe one metric calculation.

    :param name: Registered metric name, such as ``"return.simple"``.
    :type name: str
    :param window: Rolling window size in bars.
    :type window: int
    :param input_field: Numeric input field. ``"close"`` is currently supported by the Rust core.
    :type input_field: str
    :param output_name: Optional emitted metric name override.
    :type output_name: str | None
    """

    name: str
    window: int = 1
    input_field: str = "close"
    output_name: str | None = None

    def __post_init__(self) -> None:
        """Validate immutable metric configuration."""

        if not self.name:
            raise ValueError("metric name is required")
        if self.window <= 0:
            raise ValueError("metric window must be positive")

    @classmethod
    def from_value(cls, value: str | dict[str, Any] | "MetricSpec") -> "MetricSpec":
        """Normalize a user metric value into a ``MetricSpec``.

        :param value: Metric name, spec dictionary, or existing ``MetricSpec``.
        :type value: str | dict[str, Any] | MetricSpec
        :returns: Normalized metric specification.
        :rtype: MetricSpec
        """

        if isinstance(value, MetricSpec):
            return value
        if isinstance(value, str):
            return cls(value)
        return cls(
            name=value["name"],
            window=int(value.get("window", 1)),
            input_field=value.get("input_field", "close"),
            output_name=value.get("output_name"),
        )

    def to_rust(self) -> dict[str, Any]:
        """Return the dictionary shape consumed by the Rust core.

        :returns: Rust-compatible metric spec dictionary.
        :rtype: dict[str, Any]
        """

        return {
            "name": self.name,
            "window": self.window,
            "input_field": self.input_field,
            "output_name": self.output_name or self.name,
        }
