<p align="center">
  <img src="https://raw.githubusercontent.com/avi2413/fincore/main/docs/_static/fincore-wordmark.svg" alt="fincore wordmark" width="100%">
</p>

<p align="center">
  <a href="https://pypi.org/project/fincore-py/"><img src="https://img.shields.io/pypi/v/fincore-py.svg?color=111111&label=PyPI&logo=pypi&logoColor=white" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/fincore-py"><img src="https://static.pepy.tech/badge/fincore-py/month" alt="Monthly downloads"></a>
  <a href="https://pypi.org/project/fincore-py/#history"><img src="https://img.shields.io/badge/PyPI-dev%20builds-7A1E1E?logo=pypi&logoColor=white" alt="PyPI dev builds"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.14-111111?logo=python&logoColor=white" alt="Python 3.14"></a>
  <a href="https://www.rust-lang.org/"><img src="https://img.shields.io/badge/rust-core-7A1E1E?logo=rust&logoColor=white" alt="Rust core"></a>
  <a href="https://kafka.apache.org/"><img src="https://img.shields.io/badge/kafka-optional-111111?logo=apachekafka&logoColor=white" alt="Optional Kafka support"></a>
  <a href="https://pypi.org/project/fincore-py/"><img src="https://img.shields.io/badge/status-beta-111111?logo=semanticrelease&logoColor=white" alt="Beta status"></a>
  <a href="https://github.com/avi2413/fincore/actions/workflows/ci.yml"><img src="https://github.com/avi2413/fincore/actions/workflows/ci.yml/badge.svg" alt="CI workflow"></a>
  <a href="https://codecov.io/gh/avi2413/fincore"><img src="https://codecov.io/gh/avi2413/fincore/branch/main/graph/badge.svg" alt="Codecov coverage"></a>
  <a href="https://github.com/avi2413/fincore/actions/workflows/docs.yml"><img src="https://github.com/avi2413/fincore/actions/workflows/docs.yml/badge.svg" alt="Docs workflow"></a>
  <a href="https://avi2413.github.io/fincore/"><img src="https://img.shields.io/badge/docs-GitHub%20Pages-111111?logo=githubpages&logoColor=white" alt="Documentation"></a>
  <a href="https://github.com/avi2413/fincore/issues"><img src="https://img.shields.io/github/issues/avi2413/fincore.svg?color=7A1E1E&logo=github&logoColor=white" alt="GitHub issues"></a>
  <a href="https://github.com/avi2413/fincore/blob/main/LICENSE"><img src="https://img.shields.io/github/license/avi2413/fincore.svg?color=111111&logo=opensourceinitiative&logoColor=white" alt="License"></a>
</p>

# fincore

`fincore` is an event-driven financial data and analytics framework for building real-time market infrastructure.

The package is designed for software and data engineers who think in streams, schemas, event envelopes, metrics, and downstream storage. It provides a low-barrier way to build market-data pipelines: resolve `"Apple"` to `AAPL`, fetch or replay bars, emit Kafka-ready events, derive normalized analytics events, and feed those events into notebooks, databases, stream processors, or future inference systems.

This is a personal research project by Avinash Chandra and a beta-stage package. It is not a production-grade market data client, trading system, investment tool, or source of financial advice. Free public data sources can be delayed, incomplete, rate limited, schema-changing, or unavailable.

The Python import name is `fincore`. The PyPI distribution name is `fincore-py`.

## Current Scope

`fincore-py` currently focuses on data access, event streams, and metrics. It does not do trading, order execution, portfolio construction, or investment recommendations.

Implemented today:

- Stock and ETF discovery across US, Australian, and Indian market contexts.
- Bond/yield series discovery for public US Treasury FRED series.
- Fuzzy instrument search and symbol resolution.
- Yahoo Finance OHLCV bars for daily and intraday intervals.
- FRED Treasury yield observations.
- Historical replay streams.
- Delayed polling streams for latest bars.
- Kafka-ready event envelopes.
- Optional Kafka sink via `fincore-py[kafka]`.
- Batch and streaming metric events via `fincore.analytics`.
- Sphinx documentation under `docs/`.

Reserved for later:

- TimescaleDB sink.
- Additional paid/free source adapters.
- Trading or order execution, which is intentionally out of scope.

## Package Shape

```text
fincore
  data
    DataClient
    market contexts: US, AU, IN
    source descriptors
    interval/date utilities
    event envelopes
    optional Kafka sink

  analytics
    MetricEngine
    MetricSpec
    normalized metric events
    external row normalization

Rust extension
  Yahoo Finance bar fetching
  Nasdaq Trader, ASX, and NSE directory parsing
  FRED yield fetching
  metric calculations
  normalized Python dict conversion
```

## Installation

Install from PyPI:

```bash
python --version  # requires Python 3.14
python -m pip install fincore-py
```

Kafka support:

```bash
python -m pip install "fincore-py[kafka]"
```

For local development, create and activate a Python environment, then install build dependencies:

```bash
python --version  # requires Python 3.14
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

Local Kafka development:

```bash
python -m pip install -r requirements-kafka.txt
```

Docs support:

```bash
python -m pip install -r requirements-docs.txt
```

Test support:

```bash
python -m pip install -e ".[test]"
tox
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

More complete examples live in [`examples/`](examples/).

Choose a market context:

```python
us = DataClient(market="US")
au = DataClient(market="AU")
india = DataClient(market="IN")

au.search_instruments("bhp", limit=5)
india.search_instruments("reliance", limit=5)
```

Fetch daily bars:

```python
bars = client.fetch_bars("Apple", "2024-01-01", "2024-01-10")
bars[:2]
```

Fetch Australian and Indian equities using names or exchange symbols:

```python
au_bars = DataClient(market="AU").fetch_bars("BHP", "2024-01-01", "2024-01-10")
in_bars = DataClient(market="IN").fetch_bars("Reliance", "2024-01-01", "2024-01-10")
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

## Market Contexts

`DataClient` defaults to the US market:

```python
client = DataClient()
```

Supported market contexts:

```text
US  United States
AU  Australia
IN  India
```

The client uses the market context for instrument discovery and Yahoo symbol resolution:

```text
US  AAPL          -> AAPL
AU  BHP          -> BHP.AX
IN  RELIANCE     -> RELIANCE.NS
```

You can also request a global discovery context:

```python
client = DataClient(market="all")
client.search_instruments("bhp", markets=["US", "AU"])
```

Current free source choices:

```text
US instruments    Nasdaq Trader symbol directories
AU instruments    ASX listed companies CSV
IN instruments    NSE equity list CSV
Bars              Yahoo Finance chart endpoint
US bond yields    FRED public CSV
```

## Data Sources And Limitations

`fincore-py` currently prefers free, public, and low-friction sources:

```text
Nasdaq Trader   US stock and ETF discovery
ASX             Australian stock and ETF discovery
NSE             Indian equity discovery
Yahoo Finance   OHLCV bars for supported Yahoo symbols and intervals
FRED            Public US Treasury yield observations
```

These sources are suitable for learning, prototyping, personal research, notebook exploration, stream-shape design, and downstream pipeline experiments. They are not a substitute for licensed exchange feeds, paid institutional datasets, audited historical data, or production trading infrastructure.

Important limitations:

- streams are delayed polling streams, not real exchange feeds
- intraday availability depends on Yahoo's retention windows
- source files and response schemas may change without notice
- AU and IN bars depend on Yahoo suffix coverage such as `.AX` and `.NS`
- current bond/yield support is US Treasury/FRED focused
- no data completeness, survivorship-bias, corporate-action, or split-adjustment guarantees are provided

## Output Shapes

All public data methods return plain Python dictionaries. The schema is intentionally simple so downstream systems can serialize it to Kafka, JSONL, TimescaleDB, or future metric engines.

Instrument:

```python
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
```

Bar:

```python
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
```

Bond yield observation:

```python
{
    "source": "fred",
    "series_id": "DGS10",
    "date": "2024-01-02",
    "value": 4.0,
    "received_time": "2024-01-02T00:00:00+00:00",
    "raw": "2024-01-02,4.0",
}
```

Stream events use the envelope shape below, with source-specific values nested in `payload`:

```python
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
```

Metric event:

```python
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
    },
    "metadata": {
        "interval": "1d",
    },
}
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
- analytics calculations and metric events

Docs are deployed to GitHub Pages from `.github/workflows/docs.yml` on pushes to `main`, version tags, and manual dispatch.

## Testing

The unit tests run through `tox` and avoid live network calls by stubbing the Rust-backed source functions:

```bash
python -m pip install -e ".[test]"
tox
```

CI runs `tox`, `cargo fmt --check`, and `cargo check` from `.github/workflows/ci.yml`.

## Analytics

`fincore.analytics` consumes normalized bars, stream envelopes, or external row mappings. Python owns the API and state management; the numeric batch calculations run in the Rust extension.

Batch metrics:

```python
from fincore.analytics import MetricEngine, MetricSpec

engine = MetricEngine()

events = engine.compute(
    bars,
    metrics=[
        "return.simple",
        "return.log",
        MetricSpec("momentum.roc", window=3),
        MetricSpec("volatility.rolling", window=5),
        MetricSpec("auc.window", window=5),
    ],
)
```

Streaming metrics:

```python
async for bar_event in client.replay_bars("Apple", "2024-01-01", "2024-01-10"):
    for metric_event in engine.update(bar_event):
        print(metric_event)
```

External rows, for example from a database:

```python
events = engine.compute(
    db_rows,
    field_map={
        "symbol": "ticker",
        "event_time": "ts",
        "close": "close_price",
        "volume": "volume",
    },
)
```

Implemented metric families:

- returns and log returns
- momentum
- first derivative / velocity
- second derivative / acceleration
- rolling volatility
- AUC over rolling price windows
- current drawdown

Planned next:

- yield spreads
- VWAP and volume metrics
- realized volatility variants
- direction and trend-regime signals
- linked temporal graph snapshots

The goal is custom analytics on the fly for streaming data:

```python
async for metric_event in engine.run(client.stream_bars(["Apple"], interval="1m")):
    ...
```

## Contributions And Issues

Issues, bug reports, documentation fixes, and focused feature suggestions are welcome through [GitHub Issues](https://github.com/avi2413/fincore/issues).

This is still a personal research project, so contributions should stay aligned with the current scope: event-driven market data access, normalized schemas, streaming events, Kafka integration, and analytics metrics. Production trading, order execution, and investment advice are intentionally out of scope.

## Status

Beta implementation stage. The data client is usable for discovery, historical bars, yield series, replay streams, polling streams, and Kafka publishing for personal research and prototyping. The analytics layer emits normalized metric events for batch and streaming workflows.
