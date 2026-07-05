Getting started
===============

Installation
------------

Install the base local package from the repository root:

.. code-block:: bash

   python -m pip install -r requirements.txt
   python -m pip install -e .

Install Kafka support:

.. code-block:: bash

   python -m pip install -r requirements-kafka.txt

Because the package includes a Rust extension, local editable installs rebuild
the compiled module. Restart notebooks after reinstalling.

Basic usage
-----------

.. code-block:: python

   from fincore.data import DataClient

   client = DataClient()
   client.search_instruments("apple", limit=5)

Market context
--------------

``DataClient`` defaults to the US market:

.. code-block:: python

   client = DataClient()

Choose Australia or India:

.. code-block:: python

   au = DataClient(market="AU")
   india = DataClient(market="IN")

   au.search_instruments("bhp", limit=5)
   india.search_instruments("reliance", limit=5)

Fetch daily bars:

.. code-block:: python

   bars = client.fetch_bars("Apple", "2024-01-01", "2024-01-10")
   bars[:2]

Fetch Australian or Indian equities:

.. code-block:: python

   au_bars = DataClient(market="AU").fetch_bars("BHP", "2024-01-01", "2024-01-10")
   in_bars = DataClient(market="IN").fetch_bars("Reliance", "2024-01-01", "2024-01-10")

Fetch intraday bars:

.. code-block:: python

   bars = client.fetch_bars(
       "AAPL",
       "2024-01-02 09:30",
       "2024-01-02 16:00",
       interval="5m",
   )

Replay historical data as a stream:

.. code-block:: python

   async for event in client.replay_bars("Apple", "2024-01-01", "2024-01-05"):
       print(event)

Poll latest delayed bars:

.. code-block:: python

   async for event in client.stream_bars(["Apple"], interval="1m", lookback="1d"):
       print(event)
