import os
import argparse
import pickle
import json
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# Disable TensorFlow warnings for cleaner output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

from utils import calculate_indicators

# Create directories if they don't exist
os.makedirs('data', exist_ok=True)
os.makedirs('models', exist_ok=True)

def fetch_and_prepare_data(ticker, period="5y"):
    """
    Fetch stock data and compute technical indicators.
    """
    print(f"Fetching data for {ticker} (Period: {period})...")
    df = yf.download(ticker, period=period)
    
    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'. Please check the symbol.")

    # Flatten MultiIndex columns if present (sometimes returned by yfinance)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df.reset_index()
    # Calculate indicators
    df = calculate_indicators(df)
    
    # Drop rows with NaN (due to moving averages, RSI, etc.)
    df = df.dropna().reset_index(drop=True)
    return df

def prepare_ml_data(df, feature_cols, target_col='Close', lookback=1):
    """
    Prepare data for traditional ML models (LR, RF, XGBoost).
    We predict target_col at time t + 1 using features at time t.
    """
    X = df[feature_cols].copy()
    y = df[target_col].shift(-1) # Shift target by -1 to predict next day's price
    
    # Drop the last row because its target is NaN (since we shifted by -1)
    X = X.iloc[:-1]
    y = y.iloc[:-1]
    
    return X, y

def prepare_lstm_data(df, feature_cols, target_col='Close', seq_len=60):
    """
    Prepare sequential data for LSTM.
    We use a window of length seq_len (from t-seq_len to t-1) of features to predict target at t.
    """
    # Scale features and target separately
    scaler_x = MinMaxScaler(feature_range=(0, 1))
    scaler_y = MinMaxScaler(feature_range=(0, 1))
    
    # Fit scalers
    scaled_x = scaler_x.fit_transform(df[feature_cols])
    scaled_y = scaler_y.fit_transform(df[[target_col]])
    
    X_seq = []
    y_seq = []
    
    for i in range(seq_len, len(df)):
        X_seq.append(scaled_x[i-seq_len:i])
        y_seq.append(scaled_y[i, 0])
        
    return np.array(X_seq), np.array(y_seq), scaler_x, scaler_y

def train_models(ticker="AAPL", period="5y", lstm_epochs=10, lstm_batch_size=32):
    """
    Train LR, RF, XGBoost, and LSTM models and save them.
    """
    df = fetch_and_prepare_data(ticker, period)
    
    # Define features
    feature_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 
                    'SMA_20', 'EMA_50', 'RSI', 'MACD', 'MACD_Signal', 
                    'BB_Upper', 'BB_Lower']
    
    target_col = 'Close'
    
    # Create models folder specific to the ticker
    ticker_dir = os.path.join('models', ticker)
    os.makedirs(ticker_dir, exist_ok=True)
    
    print("\n--- Preprocessing & Scaling Data ---")
    
    # ----------------------------------------------------
    # DATA SPLIT FOR ML MODELS (LR, RF, XGBoost)
    # ----------------------------------------------------
    X_ml, y_ml = prepare_ml_data(df, feature_cols, target_col)
    
    # Split chronologically (80% train, 20% test)
    split_idx_ml = int(len(X_ml) * 0.8)
    
    X_train_ml, X_test_ml = X_ml.iloc[:split_idx_ml], X_ml.iloc[split_idx_ml:]
    y_train_ml, y_test_ml = y_ml.iloc[:split_idx_ml], y_ml.iloc[split_idx_ml:]
    
    # Scale ML data
    scaler_x_ml = MinMaxScaler()
    scaler_y_ml = MinMaxScaler()
    
    X_train_ml_scaled = scaler_x_ml.fit_transform(X_train_ml)
    X_test_ml_scaled = scaler_x_ml.transform(X_test_ml)
    
    y_train_ml_scaled = scaler_y_ml.fit_transform(y_train_ml.values.reshape(-1, 1)).flatten()
    y_test_ml_scaled = scaler_y_ml.transform(y_test_ml.values.reshape(-1, 1)).flatten()

    # Save scalers for ML
    with open(os.path.join(ticker_dir, 'ml_scalers.pkl'), 'wb') as f:
        pickle.dump({'scaler_x': scaler_x_ml, 'scaler_y': scaler_y_ml}, f)

    # ----------------------------------------------------
    # DATA SPLIT FOR LSTM
    # ----------------------------------------------------
    seq_len = 60
    X_lstm, y_lstm, scaler_x_lstm, scaler_y_lstm = prepare_lstm_data(df, feature_cols, target_col, seq_len)
    
    split_idx_lstm = int(len(X_lstm) * 0.8)
    
    X_train_lstm, X_test_lstm = X_lstm[:split_idx_lstm], X_lstm[split_idx_lstm:]
    y_train_lstm, y_test_lstm = y_lstm[:split_idx_lstm], y_lstm[split_idx_lstm:]
    
    # Save scalers for LSTM
    with open(os.path.join(ticker_dir, 'lstm_scalers.pkl'), 'wb') as f:
        pickle.dump({'scaler_x': scaler_x_lstm, 'scaler_y': scaler_y_lstm}, f)
        
    metrics = {}
    
    # ----------------------------------------------------
    # 1. LINEAR REGRESSION
    # ----------------------------------------------------
    print("\nTraining Linear Regression...")
    lr_model = LinearRegression()
    lr_model.fit(X_train_ml_scaled, y_train_ml_scaled)
    
    # Evaluate
    y_pred_scaled = lr_model.predict(X_test_ml_scaled)
    y_pred = scaler_y_ml.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
    
    metrics['Linear Regression'] = {
        'MAE': mean_absolute_error(y_test_ml, y_pred),
        'MSE': mean_squared_error(y_test_ml, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test_ml, y_pred)),
        'R2': r2_score(y_test_ml, y_pred)
    }
    
    # Save Model
    with open(os.path.join(ticker_dir, 'linear_regression.pkl'), 'wb') as f:
        pickle.dump(lr_model, f)
        
    # ----------------------------------------------------
    # 2. RANDOM FOREST REGRESSOR
    # ----------------------------------------------------
    print("Training Random Forest...")
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train_ml_scaled, y_train_ml_scaled)
    
    y_pred_scaled = rf_model.predict(X_test_ml_scaled)
    y_pred = scaler_y_ml.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
    
    metrics['Random Forest'] = {
        'MAE': mean_absolute_error(y_test_ml, y_pred),
        'MSE': mean_squared_error(y_test_ml, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test_ml, y_pred)),
        'R2': r2_score(y_test_ml, y_pred)
    }
    
    with open(os.path.join(ticker_dir, 'random_forest.pkl'), 'wb') as f:
        pickle.dump(rf_model, f)
        
    # ----------------------------------------------------
    # 3. XGBOOST REGRESSOR
    # ----------------------------------------------------
    print("Training XGBoost...")
    xgb_model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6, random_state=42, n_jobs=-1)
    xgb_model.fit(X_train_ml_scaled, y_train_ml_scaled)
    
    y_pred_scaled = xgb_model.predict(X_test_ml_scaled)
    y_pred = scaler_y_ml.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
    
    metrics['XGBoost'] = {
        'MAE': mean_absolute_error(y_test_ml, y_pred),
        'MSE': mean_squared_error(y_test_ml, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test_ml, y_pred)),
        'R2': r2_score(y_test_ml, y_pred)
    }
    
    with open(os.path.join(ticker_dir, 'xgboost.pkl'), 'wb') as f:
        pickle.dump(xgb_model, f)

    # ----------------------------------------------------
    # 4. LSTM NEURAL NETWORK
    # ----------------------------------------------------
    print("Training LSTM Neural Network...")
    lstm_model = Sequential([
        LSTM(units=50, return_sequences=True, input_shape=(X_train_lstm.shape[1], X_train_lstm.shape[2])),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25),
        Dense(units=1)
    ])
    
    lstm_model.compile(optimizer='adam', loss='mean_squared_error')
    
    early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
    
    lstm_model.fit(
        X_train_lstm, y_train_lstm,
        epochs=lstm_epochs,
        batch_size=lstm_batch_size,
        validation_data=(X_test_lstm, y_test_lstm),
        callbacks=[early_stop],
        verbose=1
    )
    
    # Evaluate LSTM
    y_pred_scaled = lstm_model.predict(X_test_lstm)
    y_pred = scaler_y_lstm.inverse_transform(y_pred_scaled).flatten()
    
    # Match the y_test for evaluation (unscale y_test_lstm)
    y_test_lstm_unscaled = scaler_y_lstm.inverse_transform(y_test_lstm.reshape(-1, 1)).flatten()
    
    metrics['LSTM'] = {
        'MAE': mean_absolute_error(y_test_lstm_unscaled, y_pred),
        'MSE': mean_squared_error(y_test_lstm_unscaled, y_pred),
        'RMSE': np.sqrt(mean_squared_error(y_test_lstm_unscaled, y_pred)),
        'R2': r2_score(y_test_lstm_unscaled, y_pred)
    }
    
    # Save LSTM model
    lstm_model.save(os.path.join(ticker_dir, 'lstm_model.keras'))
    
    # Save metrics
    with open(os.path.join(ticker_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=4)
        
    print("\n--- Training Completed Successfully! ---")
    for model_name, score in metrics.items():
        print(f"\n{model_name}:")
        print(f"  MAE:  {score['MAE']:.4f}")
        print(f"  MSE:  {score['MSE']:.4f}")
        print(f"  RMSE: {score['RMSE']:.4f}")
        print(f"  R2:   {score['R2']:.4f}")
        
    return metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train stock price prediction models.")
    parser.add_argument('--ticker', type=str, default='AAPL', help='Stock ticker symbol')
    parser.add_argument('--period', type=str, default='5y', help='Data period (e.g. 5y, 2y, 10y)')
    parser.add_argument('--epochs', type=int, default=10, help='Number of epochs for LSTM')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for LSTM')
    
    args = parser.parse_args()
    train_models(args.ticker, args.period, args.epochs, args.batch_size)
