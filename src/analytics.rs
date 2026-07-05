use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict};
use std::collections::HashMap;

#[derive(Clone, Debug)]
struct BarInput {
    symbol: String,
    event_time: String,
    interval: Option<String>,
    close: f64,
    volume: Option<f64>,
}

#[derive(Clone, Debug)]
struct MetricSpecInput {
    name: String,
    window: usize,
    output_name: String,
    input_field: String,
}

struct SymbolState {
    closes: Vec<f64>,
    event_times: Vec<String>,
    peak: f64,
}

impl SymbolState {
    fn new(close: f64) -> Self {
        Self {
            closes: Vec::new(),
            event_times: Vec::new(),
            peak: close,
        }
    }
}

fn extract_required_string(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<String> {
    dict.get_item(key)?
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("missing field '{key}'")))?
        .extract()
}

fn extract_required_f64(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<f64> {
    dict.get_item(key)?
        .ok_or_else(|| pyo3::exceptions::PyValueError::new_err(format!("missing field '{key}'")))?
        .extract()
}

fn extract_optional_string(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<Option<String>> {
    dict.get_item(key)?.map(|value| value.extract()).transpose()
}

fn extract_optional_f64(dict: &Bound<'_, PyDict>, key: &str) -> PyResult<Option<f64>> {
    match dict.get_item(key)? {
        Some(value) if !value.is_none() => value.extract().map(Some),
        _ => Ok(None),
    }
}

fn extract_bar(item: Bound<'_, PyAny>) -> PyResult<BarInput> {
    let dict = item.downcast::<PyDict>()?;
    Ok(BarInput {
        symbol: extract_required_string(dict, "symbol")?,
        event_time: extract_required_string(dict, "event_time")?,
        interval: extract_optional_string(dict, "interval")?,
        close: extract_required_f64(dict, "close")?,
        volume: extract_optional_f64(dict, "volume")?,
    })
}

fn extract_spec(item: Bound<'_, PyAny>) -> PyResult<MetricSpecInput> {
    let dict = item.downcast::<PyDict>()?;
    let name = extract_required_string(dict, "name")?;
    let window = match dict.get_item("window")? {
        Some(value) if !value.is_none() => value.extract::<usize>()?,
        _ => 1,
    };
    let output_name = match dict.get_item("output_name")? {
        Some(value) if !value.is_none() => value.extract::<String>()?,
        _ => name.clone(),
    };
    let input_field = match dict.get_item("input_field")? {
        Some(value) if !value.is_none() => value.extract::<String>()?,
        _ => "close".to_string(),
    };

    Ok(MetricSpecInput {
        name,
        window: window.max(1),
        output_name,
        input_field,
    })
}

fn mean(values: &[f64]) -> f64 {
    values.iter().sum::<f64>() / values.len() as f64
}

fn stddev(values: &[f64]) -> f64 {
    if values.len() < 2 {
        return 0.0;
    }
    let avg = mean(values);
    let variance = values
        .iter()
        .map(|value| {
            let diff = value - avg;
            diff * diff
        })
        .sum::<f64>()
        / (values.len() - 1) as f64;
    variance.sqrt()
}

fn log_return(current: f64, previous: f64) -> Option<f64> {
    if current > 0.0 && previous > 0.0 {
        Some((current / previous).ln())
    } else {
        None
    }
}

fn auc(values: &[f64]) -> f64 {
    values
        .windows(2)
        .map(|pair| (pair[0] + pair[1]) / 2.0)
        .sum()
}

fn metric_value(
    spec: &MetricSpecInput,
    state: &SymbolState,
    current: &BarInput,
) -> Option<(f64, &'static str)> {
    let closes = &state.closes;
    let len = closes.len();

    match spec.name.as_str() {
        "return.simple" => {
            if len < 2 {
                None
            } else {
                let previous = closes[len - 2];
                Some(((current.close - previous) / previous, "ratio"))
            }
        }
        "return.log" => {
            if len < 2 {
                None
            } else {
                log_return(current.close, closes[len - 2]).map(|value| (value, "log_ratio"))
            }
        }
        "momentum.roc" => {
            if len <= spec.window {
                None
            } else {
                let previous = closes[len - 1 - spec.window];
                Some(((current.close - previous) / previous, "ratio"))
            }
        }
        "momentum.derivative" | "momentum.velocity" => {
            if len < 2 {
                None
            } else {
                Some((current.close - closes[len - 2], "price_delta"))
            }
        }
        "momentum.acceleration" => {
            if len < 3 {
                None
            } else {
                let current_velocity = current.close - closes[len - 2];
                let previous_velocity = closes[len - 2] - closes[len - 3];
                Some((current_velocity - previous_velocity, "price_delta"))
            }
        }
        "volatility.rolling" => {
            if len <= spec.window {
                None
            } else {
                let start = len - 1 - spec.window;
                let returns = closes[start..]
                    .windows(2)
                    .map(|pair| (pair[1] - pair[0]) / pair[0])
                    .collect::<Vec<_>>();
                Some((stddev(&returns), "ratio"))
            }
        }
        "drawdown.current" => {
            if state.peak <= 0.0 {
                None
            } else {
                Some(((current.close - state.peak) / state.peak, "ratio"))
            }
        }
        "auc.window" => {
            if len < spec.window {
                None
            } else {
                let start = len - spec.window;
                Some((auc(&closes[start..]), "price_bars"))
            }
        }
        _ => None,
    }
}

fn push_metric_event(
    py: Python<'_>,
    events: &mut Vec<Py<PyDict>>,
    spec: &MetricSpecInput,
    bar: &BarInput,
    state: &SymbolState,
    value: f64,
    unit: &str,
) -> PyResult<()> {
    let event = PyDict::new(py);
    event.set_item("event_type", "metric")?;
    event.set_item("metric", &spec.output_name)?;
    event.set_item("metric_name", &spec.name)?;
    event.set_item("source", "fincore.analytics")?;
    event.set_item("symbol", &bar.symbol)?;
    event.set_item("event_time", &bar.event_time)?;
    event.set_item("value", value)?;
    event.set_item("unit", unit)?;

    let window = PyDict::new(py);
    window.set_item("kind", "bars")?;
    window.set_item("size", spec.window)?;
    event.set_item("window", window)?;

    let inputs = PyDict::new(py);
    inputs.set_item("input_field", &spec.input_field)?;
    inputs.set_item("close", bar.close)?;
    if let Some(previous) = state.event_times.iter().rev().nth(1) {
        inputs.set_item("previous_event_time", previous)?;
    }
    event.set_item("inputs", inputs)?;

    let metadata = PyDict::new(py);
    if let Some(interval) = &bar.interval {
        metadata.set_item("interval", interval)?;
    }
    if let Some(volume) = bar.volume {
        metadata.set_item("volume", volume)?;
    }
    event.set_item("metadata", metadata)?;

    events.push(event.into());
    Ok(())
}

#[pyfunction]
pub fn compute_bar_metrics(
    py: Python<'_>,
    bars: &Bound<'_, PyAny>,
    specs: &Bound<'_, PyAny>,
) -> PyResult<Vec<Py<PyDict>>> {
    let specs = specs
        .try_iter()?
        .map(|item| extract_spec(item?))
        .collect::<PyResult<Vec<_>>>()?;
    let mut states: HashMap<String, SymbolState> = HashMap::new();
    let mut events = Vec::new();

    for item in bars.try_iter()? {
        let bar = extract_bar(item?)?;
        let state = states
            .entry(bar.symbol.clone())
            .or_insert_with(|| SymbolState::new(bar.close));

        state.closes.push(bar.close);
        state.event_times.push(bar.event_time.clone());
        if bar.close > state.peak {
            state.peak = bar.close;
        }

        for spec in &specs {
            if let Some((value, unit)) = metric_value(spec, state, &bar) {
                push_metric_event(py, &mut events, spec, &bar, state, value, unit)?;
            }
        }
    }

    Ok(events)
}
