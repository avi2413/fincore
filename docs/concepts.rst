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

Market context
--------------

The client currently supports three market contexts:

US
    United States. Instrument discovery uses public Nasdaq Trader symbol
    directories. Yahoo symbols are usually unchanged, for example ``AAPL``.

AU
    Australia. Instrument discovery uses the public ASX listed companies CSV.
    Yahoo symbols use the ``.AX`` suffix, for example ``BHP.AX``.

IN
    India. Instrument discovery uses the NSE equity list CSV. Yahoo symbols use
    the ``.NS`` suffix, for example ``RELIANCE.NS``.

The market context is set during client creation:

.. code-block:: python

   us = DataClient(market="US")
   au = DataClient(market="AU")
   india = DataClient(market="IN")

Use ``market="all"`` to search all implemented contexts.

Analytics namespace
-------------------

``fincore.analytics`` consumes the same bars and event envelopes produced by
``fincore.data`` and emits normalized metric events. It also accepts external
rows from databases or files through field maps, so downstream applications do
not need to use ``DataClient`` directly.

Python handles metric specifications, input normalization, and streaming state.
The numeric batch calculations run in the Rust extension.

Sources
-------

Yahoo Finance
    Used for stock and ETF OHLCV bars. Supports daily and intraday chart
    intervals, subject to Yahoo's retention limits.

Nasdaq Trader Symbol Directory
    Used for public stock and ETF symbol discovery.

ASX listed companies CSV
    Used for Australian stock and ETF discovery.

NSE equity list CSV
    Used for Indian stock discovery.

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
