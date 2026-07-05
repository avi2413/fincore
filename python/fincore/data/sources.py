"""Source descriptors for fincore data access."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class YahooFinanceSource:
    """Free delayed daily market data source for US stocks and ETFs.

    :ivar name: Source adapter name.
    :vartype name: str
    """

    name: str = "yahoo"

@dataclass(frozen=True)
class FredBondSource:
    """Free public FRED CSV source for US Treasury yield series.

    :ivar name: Source adapter name.
    :vartype name: str
    """

    name: str = "fred"
