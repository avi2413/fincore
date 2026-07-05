Output schemas
==============

``fincore-py`` returns plain Python dictionaries. The shapes below are the
public contract for the current alpha data layer.

Instrument
----------

Returned by ``DataClient.list_instruments()``, ``search_instruments()``, and
``resolve_instrument()``.

.. code-block:: python

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
       "raw": "...",
   }

Search results add ``match_score`` and ``match_reason``. Resolved instruments
also add ``alternatives``.

Bar
---

Returned by ``DataClient.fetch_bars()``.

.. code-block:: python

   {
       "source": "yahoo",
       "symbol": "AAPL",
       "interval": "5m",
       "timeframe": "5m",
       "event_time": "2024-01-02T14:30:00+00:00",
       "date": "2024-01-02",
       "open": 100.0,
       "high": 101.0,
       "low": 99.5,
       "close": 100.5,
       "volume": 123456.0,
       "received_time": "2024-01-02T14:31:00+00:00",
       "raw": "...",
   }

Bond yield observation
----------------------

Returned by ``DataClient.fetch_bond_yields()``.

.. code-block:: python

   {
       "source": "fred",
       "series_id": "DGS10",
       "date": "2024-01-02",
       "value": 4.0,
       "received_time": "2024-01-02T00:00:00+00:00",
       "raw": "2024-01-02,4.0",
   }

Bar stream event
----------------

Returned by ``DataClient.replay_bars()`` and ``DataClient.stream_bars()``.

.. code-block:: python

   {
       "event_type": "bar",
       "stream_type": "historical_replay",
       "source": "yahoo",
       "symbol": "AAPL",
       "event_time": "2024-01-02T14:30:00+00:00",
       "received_time": "2024-01-02T14:31:00+00:00",
       "payload": {
           "interval": "5m",
           "timeframe": "5m",
           "date": "2024-01-02",
           "open": 100.0,
           "high": 101.0,
           "low": 99.5,
           "close": 100.5,
           "volume": 123456.0,
       },
       "raw": "...",
   }

Bond yield stream event
-----------------------

.. code-block:: python

   {
       "event_type": "bond_yield",
       "stream_type": "historical_replay",
       "source": "fred",
       "symbol": "DGS10",
       "event_time": "2024-01-02",
       "received_time": "2024-01-02T00:00:00+00:00",
       "payload": {
           "value": 4.0,
       },
       "raw": "2024-01-02,4.0",
   }

Metric event
------------

Returned by ``MetricEngine.compute()`` and ``MetricEngine.update()``.

.. code-block:: python

   {
       "event_type": "metric",
       "metric": "return.simple",
       "metric_name": "return.simple",
       "source": "fincore.analytics",
       "symbol": "AAPL",
       "event_time": "2024-01-02T00:00:00+00:00",
       "value": 0.0123,
       "unit": "ratio",
       "window": {
           "kind": "bars",
           "size": 1,
       },
       "inputs": {
           "input_field": "close",
           "close": 101.23,
           "previous_event_time": "2024-01-01T00:00:00+00:00",
       },
       "metadata": {
           "interval": "1d",
           "volume": 123456.0,
       },
   }
