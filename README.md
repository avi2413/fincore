<p align="center">
  <img src="https://raw.githubusercontent.com/avi2413/fincore/main/docs/_static/fincore-wordmark.svg" alt="fincore wordmark" width="520">
</p>

<p align="center">
  <a href="https://pypi.org/project/fincore-py/"><img src="https://img.shields.io/pypi/v/fincore-py.svg?color=111111&label=PyPI" alt="PyPI version"></a>
  <a href="https://test.pypi.org/project/fincore-py/"><img src="https://img.shields.io/badge/TestPyPI-dev-7A1E1E" alt="TestPyPI dev builds"></a>
  <a href="https://github.com/avi2413/fincore/actions/workflows/publish.yml"><img src="https://github.com/avi2413/fincore/actions/workflows/publish.yml/badge.svg" alt="Publish workflow"></a>
  <a href="https://github.com/avi2413/fincore/actions/workflows/docs.yml"><img src="https://github.com/avi2413/fincore/actions/workflows/docs.yml/badge.svg" alt="Docs workflow"></a>
  <a href="https://avi2413.github.io/fincore/"><img src="https://img.shields.io/badge/docs-GitHub%20Pages-111111" alt="Documentation"></a>
  <a href="https://github.com/avi2413/fincore/blob/main/LICENSE"><img src="https://img.shields.io/github/license/avi2413/fincore.svg?color=7A1E1E" alt="License"></a>
</p>

# fincore

`fincore` is a developer-first financial data library.

The package is designed for software and data engineers who understand systems, streams, schemas, and downstream storage, but may not yet know finance. The motive is to create a financial data product with a very low barrier of use and understanding: ask for `"Apple"`, get `AAPL`; ask for `"10 year treasury"`, get a usable yield series; ask for a recent minute range, get normalized market events that can flow into Kafka, TimescaleDB, notebooks, or future analytics.

The Python import name is `fincore`. The PyPI distribution name is planned as `fincore-py` because `fincore` is already used by another project on PyPI.

## Current Scope

`fincore-py` currently focuses on data access, not trading or portfolio analytics.

Implemented today:

- Stock and ETF discovery from public Nasdaq Trader symbol directories.
- Bond/yield series discovery for public US Treasury FRED series.
- Fuzzy instrument search and symbol resolution.
- Yahoo Finance OHLCV bars for daily and intraday intervals.
- FRED Treasury yield observations.
- Historical replay streams.
- Delayed polling streams for latest bars.
- Kafka-ready event envelopes.
- Optional Kafka sink via `fincore-py[kafka]`.
- Sphinx documentation under `docs/`.

Reserved for later:

- `fincore.analytics` for streaming and batch analytics.
- TimescaleDB sink.
- Additional paid/free source adapters.
- Trading or order execution, which is intentionally out of scope.

## Package Shape

```text
fincore
  data
    DataClient
    source descriptors
    interval/date utilities
    event envelopes
    optional Kafka sink

  analytics
    reserved for future custom metrics

Rust extension
  Yahoo Finance bar fetching
  Nasdaq Trader directory parsing
  FRED yield fetching
  normalized Python dict conversion
```

## Installation

Create and activate a Python environment, then install build dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Kafka support:

```bash
python -m pip install -r requirements-kafka.txt
```

Docs support:

```bash
python -m pip install -r requirements-docs.txt
```

This project includes a Rust extension. A working Rust toolchain is required:

```bash
rustc --version
cargo --version
```

If Python 3.14 triggers a PyO3 maximum-version warning in a custom build environment:

```bash
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
python -m pip install -e .
```

Restart notebook kernels after reinstalling because the compiled `_fincore` module may stay loaded.

## Quick Start

```python
from fincore.data import DataClient

client = DataClient()

client.search_instruments("apple", limit=5)
client.resolve_symbol("Apple")
```

Fetch daily bars:

```python
bars = client.fetch_bars("Apple", "2024-01-01", "2024-01-10")
bars[:2]
```

Fetch intraday bars:

```python
bars = client.fetch_bars(
    "AAPL",
    "2024-01-02 09:30",
    "2024-01-02 16:00",
    interval="5m",
)
```

Fetch Treasury yields:

```python
yields = client.fetch_bond_yields(
    "10 year treasury",
    start="2024-01-01",
    end="2024-01-10",
)
```

## Intervals

Yahoo Finance bars support:

```text
1m, 2m, 5m, 15m, 30m, 60m, 90m,
1h, 1d, 5d, 1wk, 1mo, 3mo
```

Aliases such as `1hour`, `1hr`, `day`, and `daily` are normalized by the Python client.

Approximate Yahoo retention limits:

```text
1m       about 7 days
2m-30m   about 60 days
60m/1h   about 730 days
daily+   much longer
```

## Streams

Historical replay:

```python
async for event in client.replay_bars(
    "Apple",
    "2024-01-02 09:30",
    "2024-01-02 16:00",
    interval="5m",
    interval_seconds=0.1,
):
    print(event)
```

Delayed polling stream:

```python
async for event in client.stream_bars(
    ["Apple", "Microsoft"],
    interval="1m",
    lookback="1d",
    poll_seconds=30,
):
    print(event)
```

`lookback` means the recent range fetched on each poll. For example, `lookback="1d"` with `interval="1m"` asks Yahoo for the latest day of one-minute bars and emits only bars that have not already been seen.

## Event Envelope

Streams emit normalized envelopes:

```python
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
    "raw": "...",
}
```

This shape is intended for downstream systems such as Kafka, TimescaleDB, stream processors, and future analytics engines.

## Kafka

```python
from fincore.data import DataClient
from fincore.data.kafka import KafkaSink

client = DataClient()
sink = KafkaSink("localhost:9092", "market.bars")

await sink.publish_stream(
    client.replay_bars("Apple", "2024-01-01", "2024-01-05")
)
```

Kafka remains optional. The core library does not require a broker.

## Documentation

Build the Sphinx docs:

```bash
python -m pip install -r requirements-docs.txt
sphinx-build -b html docs docs/_build/html
```

The docs explain:

- what the library does
- how the data model works
- market data concepts for non-finance developers
- streaming and Kafka concepts
- the current API surface
- future analytics direction

Docs are deployed to GitHub Pages from `.github/workflows/docs.yml` on pushes to `main`, version tags, and manual dispatch.

## Future Analytics Direction

`fincore.analytics` will consume the same event envelopes produced by `fincore.data`.

Planned metric families:

- returns and log returns
- rolling return
- momentum
- first derivative / velocity
- second derivative / acceleration
- rolling volatility
- realized volatility
- AUC over price, returns, and momentum
- VWAP and volume metrics
- direction and trend-regime signals

The goal is custom analytics on the fly for streaming data:

```python
async for metric_event in engine.run(client.stream_bars(["Apple"], interval="1m")):
    ...
```

## Versioning And Publishing

Python package versions are derived from git tags through `setuptools-scm`.

For the first pre-release:

```bash
git tag v0.1.0a0
git push origin v0.1.0a0
```

The publish workflow at `.github/workflows/publish.yml` builds distributions for both main pushes and version tags.

- Pushes to `main` publish development builds to TestPyPI.
- Tags like `v0.1.0a0` publish releases to PyPI.

Configure PyPI trusted publishing with:

```text
Repository: <owner>/fincore
Workflow: publish.yml
Environment: pypi
```

Configure TestPyPI trusted publishing with:

```text
Repository: avi2413/fincore
Workflow: publish.yml
Environment: testpypi
```

## Status

Early implementation stage. The data client is usable for discovery, historical bars, yield series, replay streams, polling streams, and Kafka publishing. Analytics is planned next.
