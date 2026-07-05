"""Test fixtures for fincore without live network calls."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = ROOT / "python"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))


def _install_fake_rust_core() -> None:
    """Install a fake ``fincore._fincore`` module before package import."""

    fake = types.ModuleType("fincore._fincore")
    fake.last_yahoo_args = None
    fake.last_fred_args = None

    def list_market_instruments() -> list[dict[str, Any]]:
        return [
            {
                "source": "nasdaq_trader",
                "symbol": "AAPL",
                "yahoo_symbol": "AAPL",
                "name": "Apple Inc. - Common Stock",
                "market": "US",
                "currency": "USD",
                "asset_class": "stock",
                "exchange": "NASDAQ",
                "is_etf": False,
                "raw": "AAPL|Apple Inc. - Common Stock",
            },
            {
                "source": "asx",
                "symbol": "BHP",
                "yahoo_symbol": "BHP.AX",
                "name": "BHP GROUP LIMITED",
                "market": "AU",
                "currency": "AUD",
                "asset_class": "stock",
                "exchange": "ASX",
                "is_etf": False,
                "raw": "BHP,BHP GROUP LIMITED",
            },
            {
                "source": "nse",
                "symbol": "RELIANCE",
                "yahoo_symbol": "RELIANCE.NS",
                "name": "Reliance Industries Limited",
                "market": "IN",
                "currency": "INR",
                "asset_class": "stock",
                "exchange": "NSE",
                "is_etf": False,
                "raw": "RELIANCE,Reliance Industries Limited,EQ",
            },
            {
                "source": "nasdaq_trader",
                "symbol": "QQQ",
                "yahoo_symbol": "QQQ",
                "name": "Invesco QQQ Trust",
                "market": "US",
                "currency": "USD",
                "asset_class": "etf",
                "exchange": "NASDAQ",
                "is_etf": True,
                "raw": "QQQ|Invesco QQQ Trust",
            },
        ]

    def list_bond_series() -> list[dict[str, Any]]:
        return [
            {
                "source": "fred",
                "symbol": "DGS10",
                "yahoo_symbol": "DGS10",
                "name": "10 Year Treasury Constant Maturity Rate",
                "market": "US",
                "currency": "USD",
                "asset_class": "bond",
                "maturity": "10Y",
                "is_etf": False,
            }
        ]

    def fetch_yahoo_bars(symbol: str, period1: int, period2: int, interval: str) -> list[dict[str, Any]]:
        fake.last_yahoo_args = (symbol, period1, period2, interval)
        return [
            {
                "source": "yahoo",
                "symbol": symbol,
                "interval": interval,
                "timeframe": interval,
                "event_time": "2024-01-02T14:30:00+00:00",
                "date": "2024-01-02",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 123456.0,
                "received_time": "2024-01-02T14:31:00+00:00",
                "raw": "{}",
            }
        ]

    def fetch_bond_yield_series(series_id: str, start: str | None, end: str | None) -> list[dict[str, Any]]:
        fake.last_fred_args = (series_id, start, end)
        return [
            {
                "source": "fred",
                "series_id": series_id,
                "date": "2024-01-02",
                "value": 4.0,
                "received_time": "2024-01-02T00:00:00+00:00",
                "raw": "2024-01-02,4.0",
            }
        ]

    fake.list_market_instruments = list_market_instruments
    fake.list_bond_series = list_bond_series
    fake.fetch_yahoo_bars = fetch_yahoo_bars
    fake.fetch_bond_yield_series = fetch_bond_yield_series
    sys.modules["fincore._fincore"] = fake


_install_fake_rust_core()
