"""Data access namespace for fincore."""

from __future__ import annotations

from .client import AssetType, DataClient, Fincore
from .events import bar_event, bond_yield_event
from .sources import FredBondSource, YahooFinanceSource
from .utils import (
    SUPPORTED_INTERVALS,
    coerce_date,
    coerce_datetime,
    coerce_yahoo_period,
    lookback_start,
    normalize_interval,
    normalize_search_text,
    score_instrument,
)

__all__ = [
    "AssetType",
    "DataClient",
    "Fincore",
    "FredBondSource",
    "YahooFinanceSource",
    "SUPPORTED_INTERVALS",
    "bar_event",
    "bond_yield_event",
    "coerce_date",
    "coerce_datetime",
    "coerce_yahoo_period",
    "lookback_start",
    "normalize_interval",
    "normalize_search_text",
    "score_instrument",
]
