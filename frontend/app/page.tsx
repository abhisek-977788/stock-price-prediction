"use client";

import {
  Activity,
  BarChart3,
  Brain,
  Building2,
  Globe2,
  Loader2,
  Newspaper,
  RefreshCw,
  Search,
  TrendingUp,
  WandSparkles,
} from "lucide-react";
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

type StockOption = {
  symbol: string;
  name: string;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const stockGroups: { label: string; options: StockOption[] }[] = [
  {
    label: "US market leaders",
    options: [
      { symbol: "MSFT", name: "Microsoft" },
      { symbol: "NVDA", name: "NVIDIA" },
      { symbol: "GOOGL", name: "Alphabet" },
      { symbol: "AMZN", name: "Amazon" },
      { symbol: "META", name: "Meta Platforms" },
      { symbol: "TSLA", name: "Tesla" },
      { symbol: "AVGO", name: "Broadcom" },
      { symbol: "ORCL", name: "Oracle" },
      { symbol: "ADBE", name: "Adobe" },
      { symbol: "CRM", name: "Salesforce" },
      { symbol: "NFLX", name: "Netflix" },
      { symbol: "AMD", name: "Advanced Micro Devices" },
      { symbol: "INTC", name: "Intel" },
      { symbol: "IBM", name: "IBM" },
      { symbol: "QCOM", name: "Qualcomm" },
    ],
  },
  {
    label: "Finance, healthcare, retail",
    options: [
      { symbol: "JPM", name: "JPMorgan Chase" },
      { symbol: "BAC", name: "Bank of America" },
      { symbol: "V", name: "Visa" },
      { symbol: "MA", name: "Mastercard" },
      { symbol: "BRK-B", name: "Berkshire Hathaway" },
      { symbol: "UNH", name: "UnitedHealth" },
      { symbol: "LLY", name: "Eli Lilly" },
      { symbol: "JNJ", name: "Johnson & Johnson" },
      { symbol: "PFE", name: "Pfizer" },
      { symbol: "WMT", name: "Walmart" },
      { symbol: "COST", name: "Costco" },
      { symbol: "HD", name: "Home Depot" },
      { symbol: "MCD", name: "McDonald's" },
      { symbol: "KO", name: "Coca-Cola" },
      { symbol: "PEP", name: "PepsiCo" },
    ],
  },
  {
    label: "Energy, industrials, ETFs",
    options: [
      { symbol: "XOM", name: "Exxon Mobil" },
      { symbol: "CVX", name: "Chevron" },
      { symbol: "GE", name: "GE Aerospace" },
      { symbol: "CAT", name: "Caterpillar" },
      { symbol: "BA", name: "Boeing" },
      { symbol: "SPY", name: "S&P 500 ETF" },
      { symbol: "QQQ", name: "Nasdaq 100 ETF" },
      { symbol: "DIA", name: "Dow Jones ETF" },
      { symbol: "IWM", name: "Russell 2000 ETF" },
      { symbol: "VTI", name: "Total US Market ETF" },
      { symbol: "VOO", name: "Vanguard S&P 500 ETF" },
      { symbol: "XLK", name: "Technology Select ETF" },
      { symbol: "XLF", name: "Financial Select ETF" },
      { symbol: "XLE", name: "Energy Select ETF" },
      { symbol: "ARKK", name: "ARK Innovation ETF" },
    ],
  },
  {
    label: "India / NSE",
    options: [
      { symbol: "RELIANCE.NS", name: "Reliance Industries" },
      { symbol: "TCS.NS", name: "Tata Consultancy Services" },
      { symbol: "INFY.NS", name: "Infosys" },
      { symbol: "HDFCBANK.NS", name: "HDFC Bank" },
      { symbol: "ICICIBANK.NS", name: "ICICI Bank" },
      { symbol: "SBIN.NS", name: "State Bank of India" },
      { symbol: "AXISBANK.NS", name: "Axis Bank" },
      { symbol: "KOTAKBANK.NS", name: "Kotak Mahindra Bank" },
      { symbol: "LT.NS", name: "Larsen & Toubro" },
      { symbol: "ITC.NS", name: "ITC" },
      { symbol: "HINDUNILVR.NS", name: "Hindustan Unilever" },
      { symbol: "BHARTIARTL.NS", name: "Bharti Airtel" },
      { symbol: "MARUTI.NS", name: "Maruti Suzuki" },
      { symbol: "TATAMOTORS.NS", name: "Tata Motors" },
      { symbol: "SUNPHARMA.NS", name: "Sun Pharma" },
      { symbol: "ADANIENT.NS", name: "Adani Enterprises" },
      { symbol: "ADANIPORTS.NS", name: "Adani Ports" },
      { symbol: "WIPRO.NS", name: "Wipro" },
      { symbol: "HCLTECH.NS", name: "HCLTech" },
      { symbol: "NESTLEIND.NS", name: "Nestle India" },
    ],
  },
];

const featuredSymbols = ["MSFT", "NVDA", "GOOGL", "TSLA", "RELIANCE.NS", "TCS.NS", "INFY.NS", "SPY"];
const periods = [
  { label: "1Y", value: "1y" },
  { label: "2Y", value: "2y" },
  { label: "5Y", value: "5y" },
  { label: "10Y", value: "10y" },
];
const horizons = [7, 15, 30];

const stockLookup = new Map(stockGroups.flatMap((group) => group.options.map((option) => [option.symbol, option])));

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
          <stop offset="0%" stopColor="#31d6a6" stopOpacity="0.34" />
          <stop offset="100%" stopColor="#31d6a6" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${path} L 1000 300 L 0 300 Z`} fill="url(#chartFill)" />
      <path d={path} fill="none" stroke="#31d6a6" strokeLinecap="round" strokeWidth="5" />
    </svg>
  );
}

export default function Home() {
  const [ticker, setTicker] = useState("MSFT");
  const [period, setPeriod] = useState("1y");
  const [horizon, setHorizon] = useState(30);
  const [stock, setStock] = useState<StockResponse | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState("");

  const selectedStock = stockLookup.get(ticker);

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

  async function trainSelectedTicker() {
    setTraining(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/train`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ticker,
          period: "5y",
          lstm_epochs: 5,
          lstm_batch_size: 32,
        }),
      });
      if (!response.ok) throw new Error((await response.json()).detail || "Unable to train models.");
      await loadStock(ticker, period);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to train models.");
    } finally {
      setTraining(false);
    }
  }

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadStock(ticker, period);
  }

  function chooseTicker(symbol: string) {
    setTicker(symbol);
    if (stock) loadStock(symbol, period);
  }

  const forecastModels = forecast?.forecast.length
    ? Object.keys(forecast.forecast[0]).filter((key) => key !== "Date")
    : [];
  const latestForecast = forecast?.forecast.at(-1);
  const selectedLabel = selectedStock ? `${selectedStock.name} (${selectedStock.symbol})` : ticker;

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Live market intelligence</p>
          <h1>Stock Price Predictor</h1>
          <p className="hero-text">
            Select a market symbol, analyze price action, compare trading signals, and train forecasts from the
            connected Render API.
          </p>
          <div className="symbol-strip" aria-label="Featured stock shortcuts">
            {featuredSymbols.map((symbol) => (
              <button
                className={ticker === symbol ? "symbol-chip active" : "symbol-chip"}
                key={symbol}
                onClick={() => chooseTicker(symbol)}
                type="button"
              >
                {symbol}
              </button>
            ))}
          </div>
        </div>

        <form className="control-deck" onSubmit={submitSearch}>
          <label>
            <span>Stock</span>
            <select
              aria-label="Stock symbol"
              value={ticker}
              onChange={(event) => chooseTicker(event.target.value)}
            >
              {stockGroups.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.options.map((option) => (
                    <option key={option.symbol} value={option.symbol}>
                      {option.symbol} - {option.name}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>
          <label>
            <span>History</span>
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
          </label>
          <button type="submit" disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <Search size={18} />}
            Analyze
          </button>
        </form>
      </section>

      <section className="status-band">
        <div>
          <Globe2 size={18} />
          <span>Selected</span>
          <strong>{selectedLabel}</strong>
        </div>
        <div>
          <Building2 size={18} />
          <span>Universe</span>
          <strong>{stockGroups.reduce((total, group) => total + group.options.length, 0)} symbols</strong>
        </div>
        <div>
          <Activity size={18} />
          <span>Backend</span>
          <strong>Render API</strong>
        </div>
      </section>

      {error ? <div className="alert">{error}</div> : null}

      {!stock ? (
        <section className="empty">
          <Brain size={42} />
          <h2>Choose a stock to start the analysis.</h2>
          <p>Use the selector above to load live price history, signals, sentiment, and forecast controls.</p>
          <button onClick={() => loadStock()} disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <RefreshCw size={18} />}
            Load {ticker}
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
                  <p className="panel-kicker">Price history</p>
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
                  <p className="panel-kicker">Model lab</p>
                  <h2>Forecast controls</h2>
                  <p>Train the selected ticker if forecast models are not available.</p>
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
              <div className="forecast-actions">
                <button onClick={loadForecast} disabled={forecastLoading || training} type="button">
                  {forecastLoading ? <Loader2 className="spin" size={18} /> : <Activity size={18} />}
                  Forecast
                </button>
                <button className="secondary-action" onClick={trainSelectedTicker} disabled={training || loading} type="button">
                  {training ? <Loader2 className="spin" size={18} /> : <WandSparkles size={18} />}
                  Train
                </button>
              </div>
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
              <div className="panel-title compact">
                <h2>Model metrics</h2>
                <BarChart3 size={18} />
              </div>
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
                    {stock.metrics.length ? (
                      stock.metrics.map((metric) => (
                        <tr key={metric.model}>
                          <td>{metric.model}</td>
                          <td>{formatNumber(metric.RMSE)}</td>
                          <td>{formatNumber(metric.R2, 3)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={3}>No trained model metrics yet.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </article>
            <article className="panel">
              <div className="panel-title compact">
                <h2>Recent signals</h2>
                <Activity size={18} />
              </div>
              <div className="signal-list">
                {stock.signals.length
                  ? stock.signals.slice(-5).map((signal) => (
                      <div key={signal.Date}>
                        <span>{signal.Date}</span>
                        <strong>{signal.Action}</strong>
                        <small>RSI {signal.Signal_RSI} | MACD {signal.Signal_MACD} | MA {signal.Signal_MA}</small>
                      </div>
                    ))
                  : "No trading signals returned for this selection."}
              </div>
            </article>
            <article className="panel news-panel">
              <div className="panel-title compact">
                <h2>Sentiment</h2>
                <Newspaper size={18} />
              </div>
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
