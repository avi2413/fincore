use chrono::{NaiveDate, Utc};
use serde::Deserialize;
use std::time::Duration;

use crate::errors::FincoreError;
use crate::models::{Bar, BondSeries, Instrument, Observation};

const YAHOO_CHART_URL: &str = "https://query1.finance.yahoo.com/v8/finance/chart/";
const NASDAQ_LISTED_URL: &str = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt";
const OTHER_LISTED_URL: &str = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt";
const FRED_CSV_URL: &str = "https://fred.stlouisfed.org/graph/fredgraph.csv";

#[derive(Debug, Deserialize)]
struct YahooChartResponse {
    chart: YahooChart,
}

#[derive(Debug, Deserialize)]
struct YahooChart {
    result: Option<Vec<YahooChartResult>>,
    error: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
struct YahooChartResult {
    timestamp: Option<Vec<i64>>,
    indicators: YahooIndicators,
}

#[derive(Debug, Deserialize)]
struct YahooIndicators {
    quote: Vec<YahooQuote>,
}

#[derive(Debug, Deserialize)]
struct YahooQuote {
    open: Vec<Option<f64>>,
    high: Vec<Option<f64>>,
    low: Vec<Option<f64>>,
    close: Vec<Option<f64>>,
    volume: Vec<Option<f64>>,
}

/// Build the blocking HTTP client used by the first source adapters.
///
/// :returns: Reqwest blocking client configured with timeout and user agent.
/// :rtype: Result[reqwest::blocking::Client, FincoreError]
fn http_client() -> Result<reqwest::blocking::Client, FincoreError> {
    Ok(reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(20))
        .user_agent("fincore/0.1 (+https://github.com/fincore)")
        .build()?)
}

/// Parse a strict ISO date.
///
/// :param value: Date text in ``YYYY-MM-DD`` format.
/// :type value: str
/// :returns: Parsed date.
/// :rtype: Result[NaiveDate, FincoreError]
fn parse_date(value: &str) -> Result<NaiveDate, FincoreError> {
    NaiveDate::parse_from_str(value, "%Y-%m-%d")
        .map_err(|_| FincoreError::InvalidDate(value.to_string()))
}

/// Split a simple comma-delimited source row.
///
/// :param line: Source CSV row.
/// :type line: str
/// :returns: Trimmed field slices.
/// :rtype: Vec[&str]
fn split_csv_line(line: &str) -> Vec<&str> {
    line.split(',').map(str::trim).collect()
}

/// Parse a floating-point field from a source row.
///
/// :param value: Field value.
/// :type value: str
/// :param line: Original source row used for error reporting.
/// :type line: str
/// :returns: Parsed floating-point number.
/// :rtype: Result[f64, FincoreError]
fn parse_f64(value: &str, line: &str) -> Result<f64, FincoreError> {
    value
        .parse::<f64>()
        .map_err(|_| FincoreError::InvalidCsv(line.to_string()))
}

/// Fetch daily bars from Yahoo's public chart endpoint and normalize them.
///
/// :param symbol: Canonical ticker symbol.
/// :type symbol: str
/// :param start: Inclusive start date in ``YYYY-MM-DD`` format.
/// :type start: i64
/// :param end: Inclusive end date in ``YYYY-MM-DD`` format.
/// :type end: i64
/// :param interval: Yahoo Finance chart interval.
/// :type interval: str
/// :returns: Normalized daily bars.
/// :rtype: Result[Vec[Bar], FincoreError]
pub fn fetch_yahoo_bars_impl(
    symbol: &str,
    period1: i64,
    period2: i64,
    interval: &str,
) -> Result<Vec<Bar>, FincoreError> {
    let url = format!(
        "{YAHOO_CHART_URL}{}?period1={period1}&period2={period2}&interval={}&events=history",
        urlencoding::encode(&symbol.to_uppercase()),
        urlencoding::encode(interval)
    );

    let received_time = Utc::now().to_rfc3339();
    let text = http_client()?.get(url).send()?.error_for_status()?.text()?;
    let response: YahooChartResponse =
        serde_json::from_str(&text).map_err(|_| FincoreError::InvalidCsv(text.clone()))?;

    if let Some(error) = response.chart.error {
        return Err(FincoreError::SourceUnavailable(error.to_string()));
    }

    let result = response
        .chart
        .result
        .and_then(|mut values| values.pop())
        .ok_or(FincoreError::EmptyResponse)?;
    let timestamps = result.timestamp.ok_or(FincoreError::EmptyResponse)?;
    let quote = result
        .indicators
        .quote
        .into_iter()
        .next()
        .ok_or(FincoreError::EmptyResponse)?;

    let mut bars = Vec::new();
    for (index, timestamp) in timestamps.iter().enumerate() {
        let Some(open) = quote.open.get(index).and_then(|value| *value) else {
            continue;
        };
        let Some(high) = quote.high.get(index).and_then(|value| *value) else {
            continue;
        };
        let Some(low) = quote.low.get(index).and_then(|value| *value) else {
            continue;
        };
        let Some(close) = quote.close.get(index).and_then(|value| *value) else {
            continue;
        };

        let date = chrono::DateTime::from_timestamp(*timestamp, 0)
            .ok_or_else(|| FincoreError::InvalidCsv(timestamp.to_string()))?
            .with_timezone(&Utc);

        bars.push(Bar {
            source: "yahoo".to_string(),
            symbol: symbol.to_uppercase(),
            interval: interval.to_string(),
            event_time: date.to_rfc3339(),
            date: date.date_naive().to_string(),
            open,
            high,
            low,
            close,
            volume: quote.volume.get(index).and_then(|value| *value),
            received_time: received_time.clone(),
            raw: text.clone(),
        });
    }

    if bars.is_empty() {
        return Err(FincoreError::EmptyResponse);
    }

    Ok(bars)
}

/// Fetch public stock and ETF directories from Nasdaq Trader.
///
/// :returns: Unique normalized stock and ETF instruments.
/// :rtype: Result[Vec[Instrument], FincoreError]
pub fn fetch_symbol_directory_impl() -> Result<Vec<Instrument>, FincoreError> {
    let client = http_client()?;
    let nasdaq = client
        .get(NASDAQ_LISTED_URL)
        .send()?
        .error_for_status()?
        .text()?;
    let other = client
        .get(OTHER_LISTED_URL)
        .send()?
        .error_for_status()?
        .text()?;

    let mut instruments = Vec::new();
    instruments.extend(parse_nasdaq_listed(&nasdaq));
    instruments.extend(parse_other_listed(&other));

    if instruments.is_empty() {
        return Err(FincoreError::EmptyResponse);
    }

    instruments.sort_by(|left, right| left.symbol.cmp(&right.symbol));
    instruments.dedup_by(|left, right| left.symbol == right.symbol);
    Ok(instruments)
}

/// Parse the Nasdaq-listed symbol directory.
///
/// :param text: Raw pipe-delimited source response.
/// :type text: str
/// :returns: Normalized instruments.
/// :rtype: Vec[Instrument]
fn parse_nasdaq_listed(text: &str) -> Vec<Instrument> {
    let mut instruments = Vec::new();

    for (index, line) in text.lines().enumerate() {
        if index == 0 || line.starts_with("File Creation Time") || line.trim().is_empty() {
            continue;
        }

        let fields: Vec<&str> = line.split('|').collect();
        if fields.len() < 2 || fields.get(3) == Some(&"Y") {
            continue;
        }

        let symbol = fields[0].trim();
        let name = fields[1].trim();
        let is_etf = fields.get(6).is_some_and(|value| value.trim() == "Y");

        instruments.push(Instrument {
            source: "nasdaq_trader".to_string(),
            symbol: symbol.to_string(),
            name: name.to_string(),
            asset_class: if is_etf { "etf" } else { "stock" }.to_string(),
            exchange: Some("NASDAQ".to_string()),
            is_etf,
            raw: line.to_string(),
        });
    }

    instruments
}

/// Parse the other-listed symbol directory.
///
/// :param text: Raw pipe-delimited source response.
/// :type text: str
/// :returns: Normalized instruments.
/// :rtype: Vec[Instrument]
fn parse_other_listed(text: &str) -> Vec<Instrument> {
    let mut instruments = Vec::new();

    for (index, line) in text.lines().enumerate() {
        if index == 0 || line.starts_with("File Creation Time") || line.trim().is_empty() {
            continue;
        }

        let fields: Vec<&str> = line.split('|').collect();
        if fields.len() < 7 || fields.get(6) == Some(&"Y") {
            continue;
        }

        let symbol = fields[0].trim();
        let name = fields[1].trim();
        let is_etf = fields.get(4).is_some_and(|value| value.trim() == "Y");

        instruments.push(Instrument {
            source: "nasdaq_trader".to_string(),
            symbol: symbol.to_string(),
            name: name.to_string(),
            asset_class: if is_etf { "etf" } else { "stock" }.to_string(),
            exchange: fields.get(2).map(|value| value.trim().to_string()),
            is_etf,
            raw: line.to_string(),
        });
    }

    instruments
}

/// Return the built-in Treasury yield series backed by FRED.
///
/// :returns: Supported bond/yield series.
/// :rtype: Vec[BondSeries]
pub fn bond_series_impl() -> Vec<BondSeries> {
    [
        ("DGS1MO", "1 Month Treasury Constant Maturity Rate", "1M"),
        ("DGS3MO", "3 Month Treasury Constant Maturity Rate", "3M"),
        ("DGS6MO", "6 Month Treasury Constant Maturity Rate", "6M"),
        ("DGS1", "1 Year Treasury Constant Maturity Rate", "1Y"),
        ("DGS2", "2 Year Treasury Constant Maturity Rate", "2Y"),
        ("DGS5", "5 Year Treasury Constant Maturity Rate", "5Y"),
        ("DGS10", "10 Year Treasury Constant Maturity Rate", "10Y"),
        ("DGS30", "30 Year Treasury Constant Maturity Rate", "30Y"),
    ]
    .into_iter()
    .map(|(symbol, name, maturity)| BondSeries {
        source: "fred".to_string(),
        symbol: symbol.to_string(),
        name: name.to_string(),
        maturity: maturity.to_string(),
    })
    .collect()
}

/// Fetch a FRED series and normalize observations.
///
/// :param series_id: FRED series identifier.
/// :type series_id: str
/// :param start: Optional inclusive start date in ``YYYY-MM-DD`` format.
/// :type start: Option[&str]
/// :param end: Optional inclusive end date in ``YYYY-MM-DD`` format.
/// :type end: Option[&str]
/// :returns: Normalized observations.
/// :rtype: Result[Vec[Observation], FincoreError]
pub fn fetch_fred_series_impl(
    series_id: &str,
    start: Option<&str>,
    end: Option<&str>,
) -> Result<Vec<Observation>, FincoreError> {
    let url = format!("{FRED_CSV_URL}?id={}", urlencoding::encode(series_id));
    let received_time = Utc::now().to_rfc3339();
    let text = http_client()?.get(url).send()?.error_for_status()?.text()?;
    let start = start.map(parse_date).transpose()?;
    let end = end.map(parse_date).transpose()?;
    let mut observations = Vec::new();

    for (index, line) in text.lines().enumerate() {
        if index == 0 || line.trim().is_empty() {
            continue;
        }

        let fields = split_csv_line(line);
        if fields.len() < 2 {
            continue;
        }

        let date = NaiveDate::parse_from_str(fields[0], "%Y-%m-%d")
            .map_err(|_| FincoreError::InvalidCsv(line.to_string()))?;
        if start.is_some_and(|value| date < value) || end.is_some_and(|value| date > value) {
            continue;
        }

        let value = if fields[1] == "." || fields[1].is_empty() {
            None
        } else {
            Some(parse_f64(fields[1], line)?)
        };

        observations.push(Observation {
            source: "fred".to_string(),
            series_id: series_id.to_uppercase(),
            date,
            value,
            received_time: received_time.clone(),
            raw: line.to_string(),
        });
    }

    if observations.is_empty() {
        return Err(FincoreError::EmptyResponse);
    }

    Ok(observations)
}
