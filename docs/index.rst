fincore-py documentation
========================

``fincore-py`` is a developer-first financial data library. It is designed for
engineers who understand data systems, streams, schemas, and downstream storage,
but may not yet know market conventions or financial terminology.

The package imports as ``fincore`` and currently focuses on:

* instrument discovery for stocks, ETFs, and public Treasury yield series
* fuzzy name resolution, such as ``"Apple"`` to ``"AAPL"``
* Yahoo Finance OHLCV bars across daily and intraday intervals
* public FRED Treasury yield observations
* historical replay streams
* delayed polling streams for latest bars
* Kafka-ready event envelopes

.. toctree::
   :maxdepth: 2
   :caption: Guide

   getting_started
   concepts
   finance_concepts
   brand
   streaming
   api
