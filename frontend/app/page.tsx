"use client";

import { Activity, BarChart3, Brain, Loader2, RefreshCw, Search, TrendingUp } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

type StockPoint = {
  Date: string;
  Close: number;
  SMA_20?: number | null;
  EMA_50?: number | null;
  RSI?: number | null;
  MACD?: number | null;
};

type Signal = {
  Date: string;
  Signal_RSI: string;
  Signal_MACD: string;
  Signal_MA: string;
  Action: string;
  Score: number;
};

type NewsItem = {
  title: string;
  publisher: string;
  link: string;
  time: string;
  sentiment: string;
  polarity: number;
};

type Metric = {
  model: string;
  MAE: number;
  MSE: number;
  RMSE: number;
  R2: number;
};

type StockResponse = {
  ticker: string;
  period: string;
  latest: {
    date: string;
    close: number;
    change: number;
    changePercent: number;
    volume: number;
    rsi: number | null;
    action: string | null;
    score: number | null;
  };
  history: StockPoint[];
  signals: Signal[];
  news: NewsItem[];
  metrics: Metric[];
};

type ForecastRow = {
  Date: string;
  [model: string]: string | number;
};

type ForecastResponse = {
  ticker: string;
  horizon: number;
  forecast: ForecastRow[];
  metrics: Metric[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const periods = [
  { label: "1Y", value: "1y" },
  { label: "2Y", value: "2y" },
  { label: "5Y", value: "5y" },
  { label: "10Y", value: "10y" },
];
const horizons = [7, 15, 30];

function formatCurrency(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function formatNumber(value?: number | null, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) return "--";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value);
}

function Sparkline({ points }: { points: StockPoint[] }) {
  const path = useMemo(() => {
    if (!points.length) return "";
    const values = points.map((point) => point.Close);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const spread = max - min || 1;
    return values
      .map((value, index) => {
        const x = (index / Math.max(values.length - 1, 1)) * 1000;
        const y = 260 - ((value - min) / spread) * 220;
        return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(" ");
  }, [points]);

  return (
    <svg className="chart" viewBox="0 0 1000 300" role="img" aria-label="Closing price trend">
      <defs>
        <linearGradient id="chartFill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#37b6ff" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#37b6ff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${path} L 1000 300 L 0 300 Z`} fill="url(#chartFill)" />
      <path d={path} fill="none" stroke="#37b6ff" strokeLinecap="round" strokeWidth="5" />
    </svg>
  );
}

export default function Home() {
  const [ticker, setTicker] = useState("AAPL");
  const [period, setPeriod] = useState("1y");
  const [horizon, setHorizon] = useState(30);
  const [stock, setStock] = useState<StockResponse | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadStock(nextTicker = ticker, nextPeriod = period) {
    setLoading(true);
    setError("");
    setForecast(null);
    try {
      const response = await fetch(
        `${API_BASE}/api/stock?ticker=${encodeURIComponent(nextTicker)}&period=${encodeURIComponent(nextPeriod)}`,
      );
      if (!response.ok) throw new Error((await response.json()).detail || "Unable to load stock data.");
      setStock(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load stock data.");
    } finally {
      setLoading(false);
    }
  }

  async function loadForecast() {
    setForecastLoading(true);
    setError("");
    try {
      const response = await fetch(
        `${API_BASE}/api/forecast?ticker=${encodeURIComponent(ticker)}&period=5y&horizon=${horizon}`,
      );
      if (!response.ok) throw new Error((await response.json()).detail || "Unable to load forecast data.");
      setForecast(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load forecast data.");
    } finally {
      setForecastLoading(false);
    }
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadStock(ticker.trim().toUpperCase(), period);
  }

  const forecastModels = forecast?.forecast.length
    ? Object.keys(forecast.forecast[0]).filter((key) => key !== "Date")
    : [];
  const latestForecast = forecast?.forecast.at(-1);

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Market intelligence dashboard</p>
          <h1>Stock Price Predictor</h1>
        </div>
        <form className="search" onSubmit={submitSearch}>
          <input
            aria-label="Ticker symbol"
            value={ticker}
            onChange={(event) => setTicker(event.target.value.toUpperCase())}
            placeholder="AAPL"
          />
          <select
            aria-label="History period"
            value={period}
            onChange={(event) => {
              setPeriod(event.target.value);
              if (ticker) loadStock(ticker, event.target.value);
            }}
          >
            {periods.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
          <button type="submit" disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
            Analyze
          </button>
        </form>
      </section>

      {error ? <div className="alert">{error}</div> : null}

      {!stock ? (
        <section className="empty">
          <Brain size={42} />
          <h2>Run an analysis to load live market data.</h2>
          <p>The dashboard reads Yahoo Finance data from the Render backend and uses saved ML models for forecasts.</p>
          <button onClick={() => loadStock()} disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
            Load AAPL
          </button>
        </section>
      ) : (
        <>
          <section className="metrics-grid">
            <article className="metric">
              <span>Latest close</span>
              <strong>{formatCurrency(stock.latest.close)}</strong>
              <small className={stock.latest.change >= 0 ? "positive" : "negative"}>
                {formatCurrency(stock.latest.change)} ({formatNumber(stock.latest.changePercent)}%)
              </small>
            </article>
            <article className="metric">
              <span>Signal</span>
              <strong>{stock.latest.action || "Hold"}</strong>
              <small>Score {stock.latest.score ?? 0}</small>
            </article>
            <article className="metric">
              <span>RSI</span>
              <strong>{formatNumber(stock.latest.rsi)}</strong>
              <small>Relative strength index</small>
            </article>
            <article className="metric">
              <span>Volume</span>
              <strong>{formatNumber(stock.latest.volume, 0)}</strong>
              <small>{stock.latest.date}</small>
            </article>
          </section>

          <section className="workspace">
            <article className="panel chart-panel">
              <div className="panel-title">
                <div>
                  <h2>{stock.ticker} closing trend</h2>
                  <p>{stock.history.length} recent sessions from the backend</p>
                </div>
                <TrendingUp size={22} />
              </div>
              <Sparkline points={stock.history} />
            </article>

            <article className="panel forecast-panel">
              <div className="panel-title">
                <div>
                  <h2>Model forecast</h2>
                  <p>Uses saved models on Render</p>
                </div>
                <BarChart3 size={22} />
              </div>
              <div className="segmented">
                {horizons.map((days) => (
                  <button
                    className={horizon === days ? "active" : ""}
                    key={days}
                    onClick={() => setHorizon(days)}
                    type="button"
                  >
                    {days}D
                  </button>
                ))}
              </div>
              <button className="wide-action" onClick={loadForecast} disabled={forecastLoading}>
                {forecastLoading ? <Loader2 className="spin" size={18} /> : <Activity size={18} />}
                Generate forecast
              </button>
              <div className="forecast-list">
                {forecastModels.length && latestForecast
                  ? forecastModels.map((model) => (
                      <div key={model}>
                        <span>{model}</span>
                        <strong>{formatCurrency(Number(latestForecast[model]))}</strong>
                      </div>
                    ))
                  : "Forecast values appear here after the backend responds."}
              </div>
            </article>
          </section>

          <section className="lower-grid">
            <article className="panel">
              <h2>Model metrics</h2>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Model</th>
                      <th>RMSE</th>
                      <th>R2</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stock.metrics.map((metric) => (
                      <tr key={metric.model}>
                        <td>{metric.model}</td>
                        <td>{formatNumber(metric.RMSE)}</td>
                        <td>{formatNumber(metric.R2, 3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>
            <article className="panel">
              <h2>Recent signals</h2>
              <div className="signal-list">
                {stock.signals.slice(-5).map((signal) => (
                  <div key={signal.Date}>
                    <span>{signal.Date}</span>
                    <strong>{signal.Action}</strong>
                    <small>RSI {signal.Signal_RSI} | MACD {signal.Signal_MACD} | MA {signal.Signal_MA}</small>
                  </div>
                ))}
              </div>
            </article>
            <article className="panel news-panel">
              <h2>Sentiment</h2>
              <div className="news-list">
                {stock.news.length
                  ? stock.news.slice(0, 4).map((item) => (
                      <a href={item.link} key={item.link || item.title} target="_blank" rel="noreferrer">
                        <span>{item.sentiment}</span>
                        <strong>{item.title}</strong>
                        <small>{item.publisher}</small>
                      </a>
                    ))
                  : "No current news returned by the backend."}
              </div>
            </article>
          </section>
        </>
      )}
    </main>
  );
}
