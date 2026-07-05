"""Data access namespace for fincore."""

from __future__ import annotations

from .client import AssetType, DataClient, Fincore, Market
from .events import bar_event, bond_yield_event
from .sources import FredBondSource, YahooFinanceSource
from .utils import (
    SUPPORTED_INTERVALS,
    SUPPORTED_MARKETS,
    coerce_date,
    coerce_datetime,
    coerce_yahoo_period,
    lookback_start,
    normalize_interval,
    normalize_market,
    normalize_markets,
    normalize_search_text,
    score_instrument,
)

__all__ = [
    "AssetType",
    "DataClient",
    "Fincore",
    "Market",
    "FredBondSource",
    "YahooFinanceSource",
    "SUPPORTED_INTERVALS",
    "SUPPORTED_MARKETS",
    "bar_event",
    "bond_yield_event",
    "coerce_date",
    "coerce_datetime",
    "coerce_yahoo_period",
    "lookback_start",
    "normalize_interval",
    "normalize_market",
    "normalize_markets",
    "normalize_search_text",
    "score_instrument",
]
