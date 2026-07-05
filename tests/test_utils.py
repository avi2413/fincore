"""Tests for data utility normalization."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from fincore.data import (
    normalize_interval,
    normalize_market,
    normalize_markets,
)
from fincore.data.utils import coerce_yahoo_period, lookback_start


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("US", "US"),
        ("usa", "US"),
        ("Australia", "AU"),
        ("ASX", "AU"),
        ("India", "IN"),
        ("NSE", "IN"),
    ],
)
def test_normalize_market_aliases(value: str, expected: str) -> None:
    assert normalize_market(value) == expected


def test_normalize_markets_accepts_all_alias() -> None:
    assert normalize_markets("all") == {"US", "AU", "IN"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1hour", "1h"),
        ("1hr", "1h"),
        ("daily", "1d"),
        ("day", "1d"),
        ("5m", "5m"),
    ],
)
def test_normalize_interval_aliases(value: str, expected: str) -> None:
    assert normalize_interval(value) == expected


def test_invalid_interval_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="unsupported interval"):
        normalize_interval("4m")


def test_coerce_yahoo_period_rejects_intraday_ranges_beyond_retention() -> None:
    with pytest.raises(ValueError, match="supports roughly"):
        coerce_yahoo_period("2024-01-01", "2024-01-20", "1m")


def test_lookback_start_supports_hour_windows() -> None:
    end = datetime(2024, 1, 2, 12, tzinfo=timezone.utc)

    assert lookback_start("6h", end=end).hour == 6
