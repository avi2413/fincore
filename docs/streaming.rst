Streaming
=========

Historical replay
-----------------

Historical replay turns a finite historical range into an async stream:

.. code-block:: python

   async for event in client.replay_bars(
       "Apple",
       "2024-01-02 09:30",
       "2024-01-02 16:00",
       interval="5m",
       interval_seconds=0.1,
   ):
       print(event)

This is useful for testing downstream applications without waiting for the
market to move in real time.

Delayed polling stream
----------------------

``stream_bars`` repeatedly fetches a recent lookback range and emits unseen bars:

.. code-block:: python

   async for event in client.stream_bars(
       ["Apple", "Microsoft"],
       interval="1m",
       lookback="1d",
       poll_seconds=30,
   ):
       print(event)

This is not exchange-grade real-time market data. It is a free-source polling
stream designed for development, prototyping, and downstream pipeline tests.

Kafka
-----

Kafka support is optional:

.. code-block:: bash

   python -m pip install -r requirements-kafka.txt

Publish a stream:

.. code-block:: python

   from fincore.data.kafka import KafkaSink

   sink = KafkaSink("localhost:9092", "market.bars")
   await sink.publish_stream(
       client.replay_bars("Apple", "2024-01-01", "2024-01-05")
   )

TimescaleDB direction
---------------------

No TimescaleDB sink is implemented yet, but event envelopes are designed so they
can be mapped cleanly into hypertables later:

* ``event_time`` as the time column
* ``symbol`` as a partition/query dimension
* ``event_type`` as a data family
* ``payload`` as normalized values
* ``raw`` as source traceability

