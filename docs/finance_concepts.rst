Finance concepts for data developers
====================================

Instrument
----------

An instrument is a thing that can be observed or traded. In this project, the
initial instruments are:

Stock
    Ownership share in a company, such as Apple or Microsoft.

ETF
    Exchange-traded fund. A basket-like product that trades like a stock.

Bond yield series
    A time series describing interest rates for a maturity, such as the US
    10-year Treasury yield.

Ticker symbol
-------------

A ticker symbol is the compact identifier used by market data sources. ``AAPL``
is Apple's ticker. ``DGS10`` is a FRED series ID for the 10-year Treasury
constant maturity rate.

OHLCV bars
----------

OHLCV means:

Open
    First price in the interval.

High
    Highest price in the interval.

Low
    Lowest price in the interval.

Close
    Last price in the interval.

Volume
    Number of shares/contracts traded in the interval.

A one-minute bar compresses many trades into one row. A daily bar compresses a
whole trading day into one row.

Interval
--------

The interval is the bar duration:

* ``1m`` means one-minute bars
* ``5m`` means five-minute bars
* ``1h`` means one-hour bars
* ``1d`` means daily bars

Intraday data has shorter historical retention than daily data.

Returns
-------

Return measures price change. A simple return is:

.. code-block:: text

   (current_price - previous_price) / previous_price

Log returns are often used in quantitative finance because they compose neatly
over time.

Momentum
--------

Momentum measures whether price movement is persisting in a direction. A simple
momentum signal compares the current price with a past price. A derivative-based
momentum signal looks at the slope of price over recent bars.

Velocity and acceleration
-------------------------

For streaming analytics, price can be treated like a curve:

First derivative
    Direction and speed of price movement. Positive means rising; negative means
    falling.

Second derivative
    Change in the first derivative. Positive means upward movement is
    accelerating or downward movement is weakening.

This can support directional interpretations:

* rising and accelerating
* rising but weakening
* falling and accelerating
* falling but stabilizing

Volatility
----------

Volatility measures how much price or returns vary. Rolling volatility uses a
recent window of returns. Higher volatility means larger price swings and often
higher risk.

AUC
---

AUC means area under the curve. In finance analytics, it can be adapted in
several ways:

Price AUC
    Area under the price curve over a window.

Return AUC
    Area under the return curve.

Momentum AUC
    Persistence and magnitude of momentum over time.

Excess AUC
    Area between price and a baseline such as a moving average.

These are not universal finance metrics by default; they are custom analytics
building blocks that can be useful for direction and regime detection.

