use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::models::{Bar, BondSeries, Instrument, Observation};

/// Convert a normalized Rust bar into a Python dictionary.
///
/// :param py: Active Python interpreter token supplied by PyO3.
/// :type py: Python
/// :param bar: Normalized Rust bar.
/// :type bar: Bar
/// :returns: Python dictionary owned by the interpreter.
/// :rtype: Py[PyDict]
pub fn bar_to_py(py: Python<'_>, bar: &Bar) -> PyResult<Py<PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("source", &bar.source)?;
    dict.set_item("symbol", &bar.symbol)?;
    dict.set_item("interval", &bar.interval)?;
    dict.set_item("timeframe", &bar.interval)?;
    dict.set_item("event_time", &bar.event_time)?;
    dict.set_item("date", &bar.date)?;
    dict.set_item("open", bar.open)?;
    dict.set_item("high", bar.high)?;
    dict.set_item("low", bar.low)?;
    dict.set_item("close", bar.close)?;
    dict.set_item("volume", bar.volume)?;
    dict.set_item("received_time", &bar.received_time)?;
    dict.set_item("raw", &bar.raw)?;
    Ok(dict.into())
}

/// Convert normalized instrument metadata into a Python dictionary.
///
/// :param py: Active Python interpreter token supplied by PyO3.
/// :type py: Python
/// :param instrument: Normalized Rust instrument metadata.
/// :type instrument: Instrument
/// :returns: Python dictionary owned by the interpreter.
/// :rtype: Py[PyDict]
pub fn instrument_to_py(py: Python<'_>, instrument: &Instrument) -> PyResult<Py<PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("source", &instrument.source)?;
    dict.set_item("symbol", &instrument.symbol)?;
    dict.set_item("yahoo_symbol", &instrument.yahoo_symbol)?;
    dict.set_item("name", &instrument.name)?;
    dict.set_item("market", &instrument.market)?;
    dict.set_item("currency", &instrument.currency)?;
    dict.set_item("asset_class", &instrument.asset_class)?;
    dict.set_item("exchange", &instrument.exchange)?;
    dict.set_item("is_etf", instrument.is_etf)?;
    dict.set_item("raw", &instrument.raw)?;
    Ok(dict.into())
}

/// Convert a FRED bond/yield series descriptor into a Python dictionary.
///
/// :param py: Active Python interpreter token supplied by PyO3.
/// :type py: Python
/// :param bond: Supported FRED Treasury yield series.
/// :type bond: BondSeries
/// :returns: Python dictionary owned by the interpreter.
/// :rtype: Py[PyDict]
pub fn bond_to_py(py: Python<'_>, bond: &BondSeries) -> PyResult<Py<PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("source", &bond.source)?;
    dict.set_item("symbol", &bond.symbol)?;
    dict.set_item("yahoo_symbol", &bond.symbol)?;
    dict.set_item("name", &bond.name)?;
    dict.set_item("market", "US")?;
    dict.set_item("currency", "USD")?;
    dict.set_item("asset_class", "bond")?;
    dict.set_item("maturity", &bond.maturity)?;
    dict.set_item("is_etf", false)?;
    Ok(dict.into())
}

/// Convert a normalized FRED observation into a Python dictionary.
///
/// :param py: Active Python interpreter token supplied by PyO3.
/// :type py: Python
/// :param observation: Normalized FRED observation.
/// :type observation: Observation
/// :returns: Python dictionary owned by the interpreter.
/// :rtype: Py[PyDict]
pub fn observation_to_py(py: Python<'_>, observation: &Observation) -> PyResult<Py<PyDict>> {
    let dict = PyDict::new(py);
    dict.set_item("source", &observation.source)?;
    dict.set_item("series_id", &observation.series_id)?;
    dict.set_item("date", observation.date.to_string())?;
    dict.set_item("value", observation.value)?;
    dict.set_item("received_time", &observation.received_time)?;
    dict.set_item("raw", &observation.raw)?;
    Ok(dict.into())
}
