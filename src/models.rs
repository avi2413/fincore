use chrono::NaiveDate;
use serde::{Deserialize, Serialize};

/// Normalized OHLCV bar.
///
/// :ivar source: Source adapter name.
/// :vartype source: String
/// :ivar symbol: Canonical ticker symbol requested by Python.
/// :vartype symbol: String
/// :ivar interval: Bar duration, for example ``"1m"``, ``"1h"``, or ``"1d"``.
/// :vartype interval: String
/// :ivar event_time: Bar timestamp in UTC.
/// :vartype event_time: String
/// :ivar date: Calendar date derived from ``event_time`` for convenience.
/// :vartype date: String
/// :ivar open: Opening price.
/// :vartype open: f64
/// :ivar high: High price.
/// :vartype high: f64
/// :ivar low: Low price.
/// :vartype low: f64
/// :ivar close: Closing price.
/// :vartype close: f64
/// :ivar volume: Optional volume value.
/// :vartype volume: Option[f64]
/// :ivar received_time: UTC timestamp when fincore received the source payload.
/// :vartype received_time: String
/// :ivar raw: Raw source CSV row.
/// :vartype raw: String
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Bar {
    pub source: String,
    pub symbol: String,
    pub interval: String,
    pub event_time: String,
    pub date: String,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: Option<f64>,
    pub received_time: String,
    pub raw: String,
}

/// Normalized stock or ETF instrument metadata.
///
/// :ivar source: Directory source name.
/// :vartype source: String
/// :ivar symbol: Listed ticker symbol.
/// :vartype symbol: String
/// :ivar yahoo_symbol: Yahoo Finance symbol used for chart requests.
/// :vartype yahoo_symbol: String
/// :ivar name: Security name.
/// :vartype name: String
/// :ivar market: Market context, such as ``"US"``, ``"AU"``, or ``"IN"``.
/// :vartype market: String
/// :ivar currency: Trading currency where known.
/// :vartype currency: String
/// :ivar asset_class: ``"stock"`` or ``"etf"``.
/// :vartype asset_class: String
/// :ivar exchange: Optional exchange code/name.
/// :vartype exchange: Option[String]
/// :ivar is_etf: Whether the source identifies the instrument as an ETF.
/// :vartype is_etf: bool
/// :ivar raw: Raw source directory row.
/// :vartype raw: String
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Instrument {
    pub source: String,
    pub symbol: String,
    pub yahoo_symbol: String,
    pub name: String,
    pub market: String,
    pub currency: String,
    pub asset_class: String,
    pub exchange: Option<String>,
    pub is_etf: bool,
    pub raw: String,
}

/// Supported FRED Treasury yield series.
///
/// :ivar source: Source adapter name.
/// :vartype source: String
/// :ivar symbol: FRED series identifier.
/// :vartype symbol: String
/// :ivar name: Human-readable series name.
/// :vartype name: String
/// :ivar maturity: Compact maturity label, for example ``"10Y"``.
/// :vartype maturity: String
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct BondSeries {
    pub source: String,
    pub symbol: String,
    pub name: String,
    pub maturity: String,
}

/// Normalized FRED time-series observation.
///
/// :ivar source: Source adapter name.
/// :vartype source: String
/// :ivar series_id: FRED series identifier.
/// :vartype series_id: String
/// :ivar date: Observation date.
/// :vartype date: NaiveDate
/// :ivar value: Optional numeric value. FRED missing values become ``None`` in Python.
/// :vartype value: Option[f64]
/// :ivar received_time: UTC timestamp when fincore received the source payload.
/// :vartype received_time: String
/// :ivar raw: Raw source CSV row.
/// :vartype raw: String
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Observation {
    pub source: String,
    pub series_id: String,
    pub date: NaiveDate,
    pub value: Option<f64>,
    pub received_time: String,
    pub raw: String,
}
