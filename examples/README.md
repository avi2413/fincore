# fincore examples

These examples are small scripts showing the current beta surface.

Run them after installing the package:

```bash
python -m pip install fincore-py
```

For local development:

```bash
python -m pip install -e .
```

Kafka examples require the optional extra:

```bash
python -m pip install "fincore-py[kafka]"
```

Examples:

- `01_data_discovery.py`: market contexts, fuzzy symbol resolution, bars, and bond yields
- `02_batch_analytics.py`: batch metric events from historical bars
- `03_streaming_metrics.py`: historical replay plus on-the-fly metrics
- `04_external_rows.py`: analytics from database-style rows with a field map
- `05_kafka_publish.py`: publishing replay events to Kafka

The examples use free public sources, so live fetches can fail or return empty results when an upstream source is unavailable, rate-limited, or outside its retention window.
