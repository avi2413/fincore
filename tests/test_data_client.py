"""Tests for the public data client surface."""

from __future__ import annotations

import pytest

from fincore import _fincore
from fincore.data import DataClient


def test_default_client_uses_us_market() -> None:
    client = DataClient()

    symbols = {item["symbol"] for item in client.list_instruments(["stock", "etf"])}

    assert symbols == {"AAPL", "QQQ"}


@pytest.mark.parametrize(
    ("market", "query", "expected"),
    [
        ("US", "Apple", "AAPL"),
        ("Australia", "BHP", "BHP.AX"),
        ("India", "Reliance", "RELIANCE.NS"),
    ],
)
def test_resolve_symbol_uses_market_context(market: str, query: str, expected: str) -> None:
    client = DataClient(market=market)

    assert client.resolve_symbol(query, asset_types=["stock"]) == expected


def test_all_market_context_searches_across_supported_markets() -> None:
    client = DataClient(market="all")

    markets = {item["market"] for item in client.list_instruments(["stock"])}

    assert markets == {"US", "AU", "IN"}


def test_search_returns_ranked_alternatives_with_match_metadata() -> None:
    client = DataClient(market="all")

    matches = client.search_instruments("reliance", asset_types=["stock"], limit=3)

    assert matches[0]["symbol"] == "RELIANCE"
    assert matches[0]["match_score"] > 0.9
    assert matches[0]["match_reason"] in {"exact_symbol", "exact_name", "name", "symbol_name"}


def test_fetch_bars_resolves_to_yahoo_symbol() -> None:
    client = DataClient(market="AU")

    bars = client.fetch_bars("BHP", "2024-01-01", "2024-01-10", interval="day")

    assert _fincore.last_yahoo_args[0] == "BHP.AX"
    assert _fincore.last_yahoo_args[3] == "1d"
    assert bars[0]["symbol"] == "BHP.AX"
    assert bars[0]["interval"] == "1d"


def test_fetch_bond_yields_resolves_human_query() -> None:
    client = DataClient()

    observations = client.fetch_bond_yields("10 year treasury", start="2024-01-01", end="2024-01-10")

    assert _fincore.last_fred_args == ("DGS10", "2024-01-01", "2024-01-10")
    assert observations[0]["series_id"] == "DGS10"


def test_resolve_instrument_reports_alternatives() -> None:
    client = DataClient(market="all")

    resolved = client.resolve_instrument("apple", asset_types=["stock"])

    assert resolved["symbol"] == "AAPL"
    assert "alternatives" in resolved
