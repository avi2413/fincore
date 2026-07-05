mod errors;
mod models;
mod pyconvert;
mod sources;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use pyconvert::{bar_to_py, bond_to_py, instrument_to_py, observation_to_py};
use sources::{
    bond_series_impl, fetch_fred_series_impl, fetch_symbol_directory_impl, fetch_yahoo_bars_impl,
};

/// Fetch daily OHLCV bars from Yahoo Finance's public chart endpoint.
///
/// :param py: Active Python interpreter token supplied by PyO3.
/// :type py: Python
/// :param symbol: Canonical ticker symbol, for example ``"AAPL"``.
/// :type symbol: str
/// :param start: Inclusive start date in ``YYYY-MM-DD`` format.
/// :type start: int
/// :param end: Inclusive end date in ``YYYY-MM-DD`` format.
/// :type end: int
/// :param interval: Yahoo Finance chart interval.
/// :type interval: str
/// :returns: Python dictionaries containing normalized daily bars.
/// :rtype: list[dict]
#[pyfunction]
#[pyo3(signature = (symbol, period1, period2, interval))]
fn fetch_yahoo_bars(
    py: Python<'_>,
    symbol: &str,
    period1: i64,
    period2: i64,
    interval: &str,
) -> PyResult<Vec<Py<PyDict>>> {
    // Release the GIL while the blocking HTTP request and CSV parsing run.
    let bars = py.allow_threads(|| fetch_yahoo_bars_impl(symbol, period1, period2, interval))?;
    bars.iter().map(|bar| bar_to_py(py, bar)).collect()
}

/// Load stocks and ETFs from public Nasdaq Trader symbol directories.
///
/// :param py: Active Python interpreter token supplied by PyO3.
/// :type py: Python
/// :returns: Python dictionaries containing normalized instrument metadata.
/// :rtype: list[dict]
#[pyfunction]
fn list_market_instruments(py: Python<'_>) -> PyResult<Vec<Py<PyDict>>> {
    let instruments = py.allow_threads(fetch_symbol_directory_impl)?;
    instruments
        .iter()
        .map(|instrument| instrument_to_py(py, instrument))
        .collect()
}

/// Return the built-in FRED Treasury yield series directory.
///
/// :param py: Active Python interpreter token supplied by PyO3.
/// :type py: Python
/// :returns: Python dictionaries containing supported bond/yield series.
/// :rtype: list[dict]
#[pyfunction]
fn list_bond_series(py: Python<'_>) -> PyResult<Vec<Py<PyDict>>> {
    bond_series_impl()
        .iter()
        .map(|bond| bond_to_py(py, bond))
        .collect()
}

/// Fetch a FRED Treasury yield time series.
///
/// :param py: Active Python interpreter token supplied by PyO3.
/// :type py: Python
/// :param series_id: FRED series identifier, for example ``"DGS10"``.
/// :type series_id: str
/// :param start: Optional inclusive start date in ``YYYY-MM-DD`` format.
/// :type start: str | None
/// :param end: Optional inclusive end date in ``YYYY-MM-DD`` format.
/// :type end: str | None
/// :returns: Python dictionaries containing normalized observations.
/// :rtype: list[dict]
#[pyfunction]
#[pyo3(signature = (series_id, start=None, end=None))]
fn fetch_bond_yield_series(
    py: Python<'_>,
    series_id: &str,
    start: Option<&str>,
    end: Option<&str>,
) -> PyResult<Vec<Py<PyDict>>> {
    let observations = py.allow_threads(|| fetch_fred_series_impl(series_id, start, end))?;
    observations
        .iter()
        .map(|observation| observation_to_py(py, observation))
        .collect()
}

/// Python module initializer for ``fincore._fincore``.
///
/// :param module: Python module object created by PyO3.
/// :type module: PyModule
/// :returns: ``Ok(())`` when all functions are registered.
/// :rtype: PyResult[()]
#[pymodule]
fn _fincore(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(fetch_yahoo_bars, module)?)?;
    module.add_function(wrap_pyfunction!(list_market_instruments, module)?)?;
    module.add_function(wrap_pyfunction!(list_bond_series, module)?)?;
    module.add_function(wrap_pyfunction!(fetch_bond_yield_series, module)?)?;
    Ok(())
}
