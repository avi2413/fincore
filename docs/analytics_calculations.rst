Analytics calculations
======================

``fincore.analytics`` turns normalized market records into normalized metric
events. The purpose is not to predict directly. The purpose is to transform raw
price/yield observations into clean features that downstream systems can store,
stream, compare, graph, or use for inference.

Data flow
---------

The current flow is:

.. code-block:: text

   raw source row
      -> normalized bar
      -> metric specification
      -> Rust numeric calculation
      -> normalized metric event

The analytics layer accepts:

* bars from ``DataClient.fetch_bars()``
* bar stream envelopes from ``DataClient.replay_bars()`` or ``stream_bars()``
* external rows from databases, files, queues, or APIs through ``field_map``

Python handles input normalization, metric specifications, and streaming state.
Rust handles the numeric calculations over each symbol's ordered bars.

Normalized input bar
--------------------

The Rust metric core expects a normalized bar-like record:

.. code-block:: python

   {
       "symbol": "AAPL",
       "event_time": "2024-01-02T00:00:00+00:00",
       "interval": "1d",
       "close": 101.25,
       "volume": 123456.0,
   }

Only ``symbol``, ``event_time``, and ``close`` are required for the current
metric set. ``interval`` and ``volume`` are carried into metric metadata when
available.

For external rows, use a field map:

.. code-block:: python

   engine.compute(
       db_rows,
       field_map={
           "symbol": "ticker",
           "event_time": "ts",
           "close": "close_price",
           "volume": "share_volume",
       },
   )

Metric events
-------------

Every calculation emits the same event shape:

.. code-block:: python

   {
       "event_type": "metric",
       "metric": "return.simple",
       "metric_name": "return.simple",
       "source": "fincore.analytics",
       "symbol": "AAPL",
       "event_time": "2024-01-03T00:00:00+00:00",
       "value": 0.05,
       "unit": "ratio",
       "window": {
           "kind": "bars",
           "size": 1,
       },
       "inputs": {
           "input_field": "close",
           "close": 105.0,
           "previous_event_time": "2024-01-02T00:00:00+00:00",
       },
       "metadata": {
           "interval": "1d",
           "volume": 123456.0,
       },
   }

This shape is intentionally event-like because it is easy to send through
Kafka, store in TimescaleDB, or convert into graph/snapshot features later.

Windows and warm-up
-------------------

``window`` means number of bars, not clock time.

If bars are daily, ``window=5`` means five daily observations. If bars are
five-minute bars, ``window=5`` means five five-minute observations.

Some metrics require previous bars. During the warm-up period, no event is
emitted for that metric.

Examples:

* ``return.simple`` needs two bars.
* ``momentum.acceleration`` needs three bars.
* ``volatility.rolling(window=5)`` needs enough bars to form five returns.
* ``auc.window(window=5)`` needs five bars.

Current metrics
---------------

return.simple
~~~~~~~~~~~~~

Formula:

.. code-block:: text

   (current_close - previous_close) / previous_close

Meaning:
    The percentage-style price move from the previous bar to the current bar.

Unit:
    ``ratio``

Example:

.. code-block:: text

   previous_close = 100
   current_close  = 105

   return.simple = (105 - 100) / 100 = 0.05

Interpretation:
    ``0.05`` means a 5 percent move up. ``-0.02`` means a 2 percent move down.

Why it matters:
    Raw prices are not directly comparable across instruments. A 5 point move
    means something different for a 20 dollar stock and a 500 dollar stock.
    Simple returns normalize the move by the previous price.

return.log
~~~~~~~~~~

Formula:

.. code-block:: text

   ln(current_close / previous_close)

Meaning:
    The logarithmic return from the previous bar to the current bar.

Unit:
    ``log_ratio``

Example:

.. code-block:: text

   previous_close = 100
   current_close  = 105

   return.log = ln(105 / 100) = 0.04879

Interpretation:
    Positive values mean price rose; negative values mean price fell.

Why it matters:
    Log returns add cleanly across time. This is useful in quantitative finance
    when combining returns over multiple bars.

momentum.roc
~~~~~~~~~~~~

Formula:

.. code-block:: text

   (current_close - close_N_bars_ago) / close_N_bars_ago

Meaning:
    Rate of change over a selected lookback window.

Unit:
    ``ratio``

Example with ``window=3``:

.. code-block:: text

   close_3_bars_ago = 100
   current_close    = 112

   momentum.roc = (112 - 100) / 100 = 0.12

Interpretation:
    ``0.12`` means the instrument is up 12 percent over the selected window.

Why it matters:
    This is a basic momentum signal. It describes whether price has been
    persistently moving up or down across a short history, not only between the
    latest two bars.

momentum.derivative
~~~~~~~~~~~~~~~~~~~

Formula:

.. code-block:: text

   current_close - previous_close

Meaning:
    First derivative of price, approximated as the price difference between two
    adjacent bars.

Unit:
    ``price_delta``

Example:

.. code-block:: text

   previous_close = 100
   current_close  = 104

   momentum.derivative = 104 - 100 = 4

Interpretation:
    Positive means price is moving upward. Negative means price is moving
    downward.

Why it matters:
    This treats price as a curve. The first derivative is the curve's local
    direction and speed. Unlike return, it is not normalized by price.

momentum.acceleration
~~~~~~~~~~~~~~~~~~~~~

Formula:

.. code-block:: text

   current_velocity  = current_close - previous_close
   previous_velocity = previous_close - close_two_bars_ago

   acceleration = current_velocity - previous_velocity

Meaning:
    Second derivative of price, approximated as the change in consecutive price
    deltas.

Unit:
    ``price_delta``

Example:

.. code-block:: text

   close_two_bars_ago = 100
   previous_close     = 103
   current_close      = 108

   previous_velocity = 103 - 100 = 3
   current_velocity  = 108 - 103 = 5

   momentum.acceleration = 5 - 3 = 2

Interpretation:
    Positive acceleration means the move is strengthening. Negative
    acceleration means the move is weakening, or the opposite direction is
    strengthening.

Why it matters:
    Direction alone is often not enough. Acceleration helps distinguish
    ``rising and strengthening`` from ``rising but fading``.

volatility.rolling
~~~~~~~~~~~~~~~~~~

Formula:

.. code-block:: text

   returns = simple returns over the rolling window
   volatility.rolling = sample_standard_deviation(returns)

Meaning:
    Recent variability of returns.

Unit:
    ``ratio``

Example:

.. code-block:: text

   returns = [0.01, -0.02, 0.015, 0.005]
   volatility.rolling = standard deviation of returns

Interpretation:
    Higher values mean recent movement is more unstable. Lower values mean
    recent movement is tighter.

Why it matters:
    Volatility is a core market feature. It can describe risk, instability,
    regime changes, and whether price movement is calm or disorderly.

Implementation note:
    The current implementation uses sample standard deviation over simple
    returns in the selected bar window.

drawdown.current
~~~~~~~~~~~~~~~~

Formula:

.. code-block:: text

   (current_close - running_peak_close) / running_peak_close

Meaning:
    Distance from the highest close observed so far in the processed sequence.

Unit:
    ``ratio``

Example:

.. code-block:: text

   running_peak_close = 120
   current_close      = 108

   drawdown.current = (108 - 120) / 120 = -0.10

Interpretation:
    ``-0.10`` means the instrument is 10 percent below its running peak.
    ``0`` means the current close is at the running peak.

Why it matters:
    Drawdown describes damage from a peak. It is useful for trend health,
    downside pressure, and later risk/regime features.

auc.window
~~~~~~~~~~

Formula:

.. code-block:: text

   sum((price_i + price_i+1) / 2 for each adjacent pair in the window)

Meaning:
    Trapezoidal approximation of area under the close-price curve over a rolling
    window.

Unit:
    ``price_bars``

Example with closes ``[100, 110, 120]``:

.. code-block:: text

   area_1 = (100 + 110) / 2 = 105
   area_2 = (110 + 120) / 2 = 115

   auc.window = 105 + 115 = 220

Interpretation:
    A larger value means the price curve occupied a higher accumulated level
    over the window.

Why it matters:
    AUC is a compact curve-shape feature. It captures accumulated price level
    across time, not just the latest point. Later, AUC variants can be applied
    to returns, momentum, or distance from a baseline.

Batch mode
----------

Batch mode computes metrics over a finite list of bars:

.. code-block:: python

   from fincore.analytics import MetricEngine, MetricSpec

   engine = MetricEngine()
   metric_events = engine.compute(
       bars,
       metrics=[
           "return.simple",
           "return.log",
           MetricSpec("momentum.roc", window=3),
           MetricSpec("volatility.rolling", window=5),
           MetricSpec("auc.window", window=5),
       ],
   )

Use batch mode for notebooks, backfills, database extracts, and historical
research.

Streaming mode
--------------

Streaming mode updates the engine one event at a time:

.. code-block:: python

   engine = MetricEngine()

   async for event in client.replay_bars("Apple", "2024-01-01", "2024-01-10"):
       metric_events = engine.update(event)
       for metric_event in metric_events:
           print(metric_event)

The engine keeps a rolling buffer per symbol:

.. code-block:: text

   AAPL   -> recent AAPL bars
   MSFT   -> recent MSFT bars
   BHP.AX -> recent BHP.AX bars

This lets it calculate rolling and derivative metrics on the fly.

How to read metric events
-------------------------

When reading a metric event, ask:

* ``metric``: What calculation is this?
* ``symbol``: Which instrument does it describe?
* ``event_time``: Which market timestamp does it belong to?
* ``value``: What is the calculated number?
* ``unit``: How should the number be interpreted?
* ``window``: How much history was used?
* ``inputs``: Which source field was used?
* ``metadata``: What context came from the original market record?

For future inference, this gives a consistent feature stream:

.. code-block:: text

   normalized bars
      -> metric events
      -> aligned temporal snapshots
      -> linked graph state
      -> inference engine

