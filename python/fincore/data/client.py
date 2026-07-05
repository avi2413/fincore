"""Market data client for discovery, historical fetches, and streams."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable
from datetime import date, datetime, timezone
from typing import Any, Literal

from fincore import _fincore

from .events import bar_event
from .sources import FredBondSource, YahooFinanceSource
from .utils import (
    coerce_date,
    coerce_yahoo_period,
    lookback_start,
    normalize_markets,
    normalize_search_text,
    score_instrument,
)

AssetType = Literal["stock", "etf", "bond"]
Market = Literal["US", "AU", "IN"]


class DataClient:
    """Client for market data discovery, historical fetches, and simple streams."""

    def __init__(self, market: str | Iterable[str] = "US") -> None:
        """Create a data client with a market context and empty instrument cache.

        :param market: Market context such as ``"US"``, ``"AU"``, ``"IN"``, or ``"all"``.
        :type market: str | Iterable[str]
        """

        self.markets = normalize_markets(market)
        self._instrument_cache: list[dict[str, Any]] | None = None

    def list_instruments(
        self,
        asset_types: Iterable[AssetType] | None = None,
        markets: str | Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return available market instruments from free source directories.

        Stocks and ETFs are sourced from Nasdaq Trader, ASX, and NSE directories.
        Bonds are represented as FRED Treasury yield series.

        :param asset_types: Optional asset classes to include.
        :type asset_types: Iterable[AssetType] | None
        :param markets: Optional market override. Defaults to the client context.
        :type markets: str | Iterable[str] | None
        :returns: Matching instrument dictionaries.
        :rtype: list[dict[str, Any]]
        """

        requested = set(asset_types or ("stock", "etf", "bond"))
        requested_markets = self.markets if markets is None else normalize_markets(markets)
        all_instruments = self._all_instruments()
        return [
            item
            for item in all_instruments
            if item["asset_class"] in requested and item.get("market", "US") in requested_markets
        ]

    def refresh_instruments(self) -> list[dict[str, Any]]:
        """Refresh and return the locally cached source instrument directory.

        :returns: Fresh instrument directory.
        :rtype: list[dict[str, Any]]
        """

        self._instrument_cache = self._load_instruments()
        return list(self._instrument_cache)

    def search_instruments(
        self,
        query: str,
        *,
        asset_types: Iterable[AssetType] | None = None,
        markets: str | Iterable[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return the closest symbol/name matches for a human query.

        :param query: Symbol, company name, ETF name, or bond maturity query.
        :type query: str
        :param asset_types: Optional asset classes to search.
        :type asset_types: Iterable[AssetType] | None
        :param markets: Optional market override. Defaults to the client context.
        :type markets: str | Iterable[str] | None
        :param limit: Maximum number of matches to return.
        :type limit: int
        :returns: Matched instruments enriched with score and reason.
        :rtype: list[dict[str, Any]]
        :raises ValueError: If ``limit`` is not positive.
        """

        if limit <= 0:
            raise ValueError("limit must be positive")

        normalized_query = normalize_search_text(query)
        if not normalized_query:
            return []

        matches: list[dict[str, Any]] = []
        for instrument in self.list_instruments(asset_types, markets=markets):
            score, reason = score_instrument(normalized_query, instrument)
            if score <= 0:
                continue

            enriched = dict(instrument)
            enriched["match_score"] = round(score, 4)
            enriched["match_reason"] = reason
            matches.append(enriched)

        matches.sort(key=lambda item: (item["match_score"], item["symbol"]), reverse=True)
        return matches[:limit]

    def resolve_instrument(
        self,
        query: str,
        *,
        asset_types: Iterable[AssetType] | None = None,
        markets: str | Iterable[str] | None = None,
        min_score: float = 0.65,
    ) -> dict[str, Any]:
        """Resolve a symbol or fuzzy company/fund name to one instrument.

        :param query: Symbol, company name, ETF name, or bond maturity query.
        :type query: str
        :param asset_types: Optional asset classes to search.
        :type asset_types: Iterable[AssetType] | None
        :param markets: Optional market override. Defaults to the client context.
        :type markets: str | Iterable[str] | None
        :param min_score: Minimum fuzzy score required for automatic resolution.
        :type min_score: float
        :returns: Best instrument match with alternatives.
        :rtype: dict[str, Any]
        :raises ValueError: If no confident match is found.
        """

        matches = self.search_instruments(query, asset_types=asset_types, markets=markets, limit=10)
        if not matches:
            raise ValueError(f"no instruments matched {query!r}")

        best = matches[0]
        if best["match_reason"].startswith("exact") or best["match_score"] >= min_score:
            resolved = dict(best)
            resolved["alternatives"] = matches[1:]
            return resolved

        alternatives = ", ".join(f"{item['symbol']} ({item['name']})" for item in matches)
        raise ValueError(f"could not confidently resolve {query!r}; closest matches: {alternatives}")

    def resolve_symbol(
        self,
        query: str,
        *,
        asset_types: Iterable[AssetType] | None = None,
        markets: str | Iterable[str] | None = None,
        min_score: float = 0.65,
    ) -> str:
        """Resolve a human query to the canonical source symbol.

        :param query: Symbol, name, or maturity query.
        :type query: str
        :param asset_types: Optional asset classes to search.
        :type asset_types: Iterable[AssetType] | None
        :param markets: Optional market override. Defaults to the client context.
        :type markets: str | Iterable[str] | None
        :param min_score: Minimum fuzzy score required for automatic resolution.
        :type min_score: float
        :returns: Canonical source symbol.
        :rtype: str
        """

        instrument = self.resolve_instrument(
            query,
            asset_types=asset_types,
            markets=markets,
            min_score=min_score,
        )
        return instrument.get("yahoo_symbol") or instrument["symbol"]

    def list_stocks(self) -> list[dict[str, Any]]:
        """Return available stock symbols.

        :returns: Stock instrument dictionaries.
        :rtype: list[dict[str, Any]]
        """

        return self.list_instruments(["stock"])

    def list_etfs(self) -> list[dict[str, Any]]:
        """Return available ETF symbols.

        :returns: ETF instrument dictionaries.
        :rtype: list[dict[str, Any]]
        """

        return self.list_instruments(["etf"])

    def list_bonds(self) -> list[dict[str, Any]]:
        """Return supported public bond yield series.

        :returns: Bond/yield series dictionaries.
        :rtype: list[dict[str, Any]]
        """

        return self.list_instruments(["bond"])

    def fetch_bars(
        self,
        symbol: str,
        start: str,
        end: str,
        *,
        interval: str = "1d",
        source: YahooFinanceSource | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch OHLCV bars for a stock or ETF over a date/time range.

        :param symbol: Symbol or fuzzy instrument name.
        :type symbol: str
        :param start: Inclusive start date.
        :type start: str
        :param end: Inclusive end date.
        :type end: str
        :param interval: Yahoo Finance interval such as ``"1m"``, ``"5m"``, ``"1h"``, or ``"1d"``.
        :type interval: str
        :param source: Optional Yahoo Finance source descriptor.
        :type source: YahooFinanceSource | None
        :returns: Normalized daily bar dictionaries.
        :rtype: list[dict[str, Any]]
        """

        source = source or YahooFinanceSource()
        if source.name != "yahoo":
            raise ValueError(f"unsupported bar source: {source.name}")

        resolved_symbol = self.resolve_symbol(symbol, asset_types=["stock", "etf"])
        period1, period2, normalized_interval = coerce_yahoo_period(start, end, interval)
        return _fincore.fetch_yahoo_bars(
            resolved_symbol,
            period1,
            period2,
            normalized_interval,
        )

    def fetch_bond_yields(
        self,
        series_id: str,
        start: str | None = None,
        end: str | None = None,
        source: FredBondSource | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch a public Treasury yield time series from FRED.

        :param series_id: FRED series ID or fuzzy bond maturity/name query.
        :type series_id: str
        :param start: Optional inclusive start date.
        :type start: str | None
        :param end: Optional inclusive end date.
        :type end: str | None
        :param source: Optional FRED source descriptor.
        :type source: FredBondSource | None
        :returns: Normalized observation dictionaries.
        :rtype: list[dict[str, Any]]
        """

        source = source or FredBondSource()
        if source.name != "fred":
            raise ValueError(f"unsupported bond source: {source.name}")

        resolved_series = self.resolve_symbol(series_id, asset_types=["bond"])
        return _fincore.fetch_bond_yield_series(
            resolved_series,
            coerce_date(start) if start is not None else None,
            coerce_date(end) if end is not None else None,
        )

    async def replay_bars(
        self,
        symbol: str,
        start: str,
        end: str,
        *,
        interval: str = "1d",
        interval_seconds: float = 0.0,
    ) -> AsyncIterator[dict[str, Any]]:
        """Replay historical bars as an async stream.

        :param symbol: Symbol or fuzzy instrument name.
        :type symbol: str
        :param start: Inclusive start date.
        :type start: str
        :param end: Inclusive end date.
        :type end: str
        :param interval: Yahoo Finance interval.
        :type interval: str
        :param interval_seconds: Optional delay between replayed events.
        :type interval_seconds: float
        :yields: Stream event envelopes.
        :rtype: AsyncIterator[dict[str, Any]]
        """

        bars = self.fetch_bars(symbol, start, end, interval=interval)
        for bar in bars:
            yield bar_event(bar, stream_type="historical_replay")
            if interval_seconds > 0:
                await asyncio.sleep(interval_seconds)

    async def stream_bars(
        self,
        symbols: Iterable[str],
        *,
        interval: str = "1m",
        lookback: str = "1d",
        poll_seconds: float = 30.0,
    ) -> AsyncIterator[dict[str, Any]]:
        """Poll latest delayed bars and expose unseen bars as an async stream.

        Free sources generally do not provide reliable real-time stock streams.
        This method intentionally models current data as polling of delayed bars over
        a recent lookback range.

        :param symbols: Symbols or fuzzy instrument names to poll.
        :type symbols: Iterable[str]
        :param interval: Yahoo Finance interval.
        :type interval: str
        :param lookback: Recent range to request each poll, such as ``"1d"`` or ``"6h"``.
        :type lookback: str
        :param poll_seconds: Delay between polling rounds.
        :type poll_seconds: float
        :yields: Stream event envelopes.
        :rtype: AsyncIterator[dict[str, Any]]
        :raises ValueError: If ``poll_seconds`` is not positive.
        """

        if poll_seconds <= 0:
            raise ValueError("poll_seconds must be positive")

        normalized_symbols = list(symbols)
        seen: set[tuple[str, str, str]] = set()

        while True:
            end_dt = datetime.now(timezone.utc)
            start_dt = lookback_start(lookback, end=end_dt)
            for symbol in normalized_symbols:
                try:
                    bars = self.fetch_bars(symbol, start_dt, end_dt, interval=interval)
                except RuntimeError:
                    continue

                for bar in bars:
                    key = (bar["symbol"], bar["interval"], bar["event_time"])
                    if key in seen:
                        continue
                    seen.add(key)
                    yield bar_event(bar, stream_type="delayed_poll")

            await asyncio.sleep(poll_seconds)

    stream_current_bars = stream_bars

    def _all_instruments(self) -> list[dict[str, Any]]:
        if self._instrument_cache is None:
            self._instrument_cache = self._load_instruments()
        return list(self._instrument_cache)

    def _load_instruments(self) -> list[dict[str, Any]]:
        instruments: list[dict[str, Any]] = []

        for item in _fincore.list_market_instruments():
            instruments.append(item)

        instruments.extend(_fincore.list_bond_series())

        return instruments


def _today_iso() -> str:
    return date.today().isoformat()


def _recent_start_iso(days: int = 14) -> str:
    from datetime import timedelta

    return (date.today() - timedelta(days=days)).isoformat()


Fincore = DataClient
