import os
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from predict import forecast_future_prices, load_models_and_scalers
from train_model import train_models
from utils import analyze_sentiment, calculate_indicators, generate_signals


PERIODS = {"1y", "2y", "5y", "10y"}
HORIZONS = {7, 15, 30}
FEATURE_COLUMNS = [
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "SMA_20",
    "EMA_50",
    "RSI",
    "MACD",
    "MACD_Signal",
    "BB_Upper",
    "BB_Lower",
]


class TrainRequest(BaseModel):
    ticker: str = Field(default="AAPL", min_length=1, max_length=12)
    period: Literal["1y", "2y", "5y", "10y"] = "5y"
    lstm_epochs: int = Field(default=5, ge=1, le=30)
    lstm_batch_size: int = Field(default=32, ge=8, le=256)


app = FastAPI(
    title="Stock Price Prediction API",
    description="FastAPI backend for stock analysis, model metrics, training, and forecasting.",
    version="1.0.0",
)

frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")
allow_origins = ["*"] if frontend_origin == "*" else [frontend_origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_ticker(ticker: str) -> str:
    cleaned = ticker.strip().upper()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Ticker is required.")
    return cleaned


def clean_json(value):
    if isinstance(value, dict):
        return {key: clean_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_json(item) for item in value]
    if isinstance(value, tuple):
        return [clean_json(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return value


def dataframe_records(df: pd.DataFrame) -> list[dict]:
    safe_df = df.copy()
    for column in safe_df.columns:
        if pd.api.types.is_datetime64_any_dtype(safe_df[column]):
            safe_df[column] = safe_df[column].dt.strftime("%Y-%m-%d")
    safe_df = safe_df.replace([np.inf, -np.inf], np.nan)
    return clean_json(safe_df.where(pd.notnull(safe_df), None).to_dict(orient="records"))


def fetch_stock_data(ticker: str, period: str) -> pd.DataFrame:
    if period not in PERIODS:
        raise HTTPException(status_code=400, detail="Unsupported period.")

    df = yf.download(ticker, period=period, progress=False)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No market data found for {ticker}.")

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df.reset_index()
    df = calculate_indicators(df)
    return df


def load_metrics(ticker: str) -> list[dict]:
    metrics_path = os.path.join("models", ticker, "metrics.json")
    if not os.path.exists(metrics_path):
        return {}

    metrics_df = pd.read_json(metrics_path).T
    return dataframe_records(metrics_df.reset_index(names="model"))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/stock")
def get_stock(
    ticker: str = Query(default="AAPL", min_length=1, max_length=12),
    period: Literal["1y", "2y", "5y", "10y"] = "1y",
) -> dict:
    ticker = normalize_ticker(ticker)
    df = fetch_stock_data(ticker, period)
    signal_df = generate_signals(df)

    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    latest_signal = signal_df.iloc[-1] if not signal_df.empty else None
    clean_history = df.tail(180)[
        ["Date", "Open", "High", "Low", "Close", "Volume", "SMA_20", "EMA_50", "RSI", "MACD"]
    ]

    return {
        "ticker": ticker,
        "period": period,
        "latest": {
            "date": pd.to_datetime(latest["Date"]).strftime("%Y-%m-%d"),
            "close": float(latest["Close"]),
            "change": float(latest["Close"] - previous["Close"]),
            "changePercent": float(((latest["Close"] - previous["Close"]) / previous["Close"]) * 100),
            "volume": float(latest["Volume"]),
            "rsi": None if pd.isna(latest["RSI"]) else float(latest["RSI"]),
            "action": None if latest_signal is None else latest_signal.get("Action"),
            "score": None if latest_signal is None else int(latest_signal.get("Score", 0)),
        },
        "history": dataframe_records(clean_history),
        "signals": dataframe_records(
            signal_df.tail(20)[["Date", "Signal_RSI", "Signal_MACD", "Signal_MA", "Action", "Score"]]
        )
        if not signal_df.empty
        else [],
        "news": analyze_sentiment(ticker),
        "metrics": load_metrics(ticker),
    }


@app.get("/api/forecast")
def get_forecast(
    ticker: str = Query(default="AAPL", min_length=1, max_length=12),
    period: Literal["1y", "2y", "5y", "10y"] = "5y",
    horizon: Literal[7, 15, 30] = 30,
) -> dict:
    ticker = normalize_ticker(ticker)
    if horizon not in HORIZONS:
        raise HTTPException(status_code=400, detail="Unsupported horizon.")

    df = fetch_stock_data(ticker, period).dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)
    try:
        models, scalers = load_models_and_scalers(ticker)
        if not models:
            raise FileNotFoundError(f"No models loaded for {ticker}.")
        forecast_df = forecast_future_prices(df, models, scalers, ticker, horizon=horizon)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "ticker": ticker,
        "period": period,
        "horizon": horizon,
        "forecast": dataframe_records(forecast_df),
        "metrics": load_metrics(ticker),
    }


@app.post("/api/train")
def train(request: TrainRequest) -> dict:
    ticker = normalize_ticker(request.ticker)
    try:
        metrics = train_models(
            ticker=ticker,
            period=request.period,
            lstm_epochs=request.lstm_epochs,
            lstm_batch_size=request.lstm_batch_size,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"ticker": ticker, "metrics": clean_json(metrics)}
