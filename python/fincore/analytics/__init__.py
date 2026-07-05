"""Streaming and batch analytics for normalized market data."""

from __future__ import annotations

from .engine import MetricEngine
from .models import MetricSpec
from .normalize import normalize_bar

__all__ = [
    "MetricEngine",
    "MetricSpec",
    "normalize_bar",
]
