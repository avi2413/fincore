Core concepts
=============

Product motive
--------------

``fincore-py`` is meant to become a financial data product for developers who
are comfortable with data engineering but not necessarily comfortable with
finance. The design goal is a low barrier to entry: a user should be able to ask
for ``"Apple"`` or ``"10 year treasury"`` and receive structured data with
clear timestamps, symbols, payloads, and raw source context.

The library is system-centric:

* predictable Python APIs
* normalized dictionaries
* async streams
* event envelopes suitable for Kafka and TimescaleDB
* optional downstream sinks
* no required database or message broker

Data namespace
--------------

Current implemented functionality lives under ``fincore.data``.

``DataClient`` handles:

* listing instruments
* fuzzy searching instruments
* resolving human names to symbols
* fetching OHLCV bars
* fetching public Treasury yield series
* replaying historical bars as streams
* polling latest delayed bars as streams

Analytics namespace
-------------------

``fincore.analytics`` is reserved for future streaming analytics. The intended
direction is to consume the same event envelopes produced by ``fincore.data`` and
emit enriched analytics events.

Sources
-------

Yahoo Finance
    Used for stock and ETF OHLCV bars. Supports daily and intraday chart
    intervals, subject to Yahoo's retention limits.

Nasdaq Trader Symbol Directory
    Used for public stock and ETF symbol discovery.

FRED
    Used for public Treasury yield series such as ``DGS10``.

Event envelopes
---------------

Streams emit envelopes instead of raw rows:

.. code-block:: python

   {
       "event_type": "bar",
       "stream_type": "historical_replay",
       "source": "yahoo",
       "symbol": "AAPL",
       "event_time": "2024-01-02T14:30:00+00:00",
       "received_time": "...",
       "payload": {
           "interval": "5m",
           "open": 100.0,
           "high": 101.0,
           "low": 99.5,
           "close": 100.5,
           "volume": 123456,
       },
       "raw": "..."
   }

This shape is friendly to streaming systems because the event metadata is stable
and the market payload is nested.

Intervals
---------

Supported Yahoo intervals:

.. code-block:: text

   1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h,
   1d, 5d, 1wk, 1mo, 3mo

Common aliases such as ``"1hour"``, ``"1hr"``, ``"day"``, and ``"daily"`` are
normalized by the Python client.

Lookback
--------

``lookback`` is used by polling streams:

.. code-block:: python

   client.stream_bars(["Apple"], interval="1m", lookback="1d")

It means: each poll asks Yahoo for the latest one day of one-minute bars, then
emits only bars that have not already been seen. It is a data-fetching window,
not an analytics window.

