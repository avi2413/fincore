"""Discover instruments and fetch normalized data."""

from __future__ import annotations

from fincore.data import DataClient


def main() -> None:
    client = DataClient(market="US")
    print("US matches for Apple:")
    print(client.search_instruments("apple", limit=3))

    au = DataClient(market="AU")
    print("Australia matches for BHP:")
    print(au.search_instruments("bhp", limit=3))

    india = DataClient(market="IN")
    print("India matches for Reliance:")
    print(india.search_instruments("reliance", limit=3))

    print("Daily Apple bars:")
    bars = client.fetch_bars("Apple", "2024-01-01", "2024-01-10", interval="1d")
    print(bars[:2])

    print("US 10Y Treasury yield observations:")
    yields = client.fetch_bond_yields("10 year treasury", start="2024-01-01", end="2024-01-10")
    print(yields[:2])


if __name__ == "__main__":
    main()
