use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::PyErr;

/// Error type used inside the Rust core.
///
/// :ivar Http: Wrapper around source HTTP failures.
/// :ivar InvalidDate: Date parsing failure for user-provided dates.
/// :ivar EmptyResponse: Source returned no usable rows.
/// :ivar InvalidCsv: Source response did not match the expected CSV shape.
/// :ivar SourceUnavailable: Source returned an anti-bot or otherwise unusable response.
#[derive(Debug, thiserror::Error)]
pub enum FincoreError {
    #[error("http request failed: {0}")]
    Http(#[from] reqwest::Error),
    #[error("invalid date '{0}', expected YYYY-MM-DD")]
    InvalidDate(String),
    #[error("source returned no usable rows")]
    EmptyResponse,
    #[error("invalid csv response: {0}")]
    InvalidCsv(String),
    #[error("source unavailable: {0}")]
    SourceUnavailable(String),
}

/// Convert Rust core errors into Python exceptions.
///
/// :param err: Internal fincore error.
/// :type err: FincoreError
/// :returns: Python exception that PyO3 can raise.
/// :rtype: PyErr
impl From<FincoreError> for PyErr {
    fn from(err: FincoreError) -> Self {
        match err {
            FincoreError::InvalidDate(_) | FincoreError::InvalidCsv(_) => {
                PyValueError::new_err(err.to_string())
            }
            _ => PyRuntimeError::new_err(err.to_string()),
        }
    }
}
