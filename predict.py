import os
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import timedelta
from utils import calculate_indicators

def load_models_and_scalers(ticker):
    """
    Load all models and scalers for the given ticker.
    """
    ticker_dir = os.path.join('models', ticker)
    if not os.path.exists(ticker_dir):
        raise FileNotFoundError(f"No trained models found for ticker '{ticker}'. Please train the models first.")

    models = {}
    scalers = {}

    # Load ML models
    for model_name, filename in [
        ('Linear Regression', 'linear_regression.pkl'),
        ('Random Forest', 'random_forest.pkl'),
        ('XGBoost', 'xgboost.pkl')
    ]:
        filepath = os.path.join(ticker_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                models[model_name] = pickle.load(f)

    # Load LSTM model
    lstm_path = os.path.join(ticker_dir, 'lstm_model.keras')
    if os.path.exists(lstm_path):
        try:
            models['LSTM'] = tf.keras.models.load_model(lstm_path)
        except Exception as e:
            print(f"Error loading LSTM model: {e}")

    # Load scalers
    ml_scalers_path = os.path.join(ticker_dir, 'ml_scalers.pkl')
    if os.path.exists(ml_scalers_path):
        with open(ml_scalers_path, 'rb') as f:
            scalers['ML'] = pickle.load(f)

    lstm_scalers_path = os.path.join(ticker_dir, 'lstm_scalers.pkl')
    if os.path.exists(lstm_scalers_path):
        with open(lstm_scalers_path, 'rb') as f:
            scalers['LSTM'] = pickle.load(f)

    return models, scalers

def forecast_future_prices(df_history, models, scalers, ticker, horizon=30):
    """
    Generate future price forecasts using a recursive roll-forward mechanism.
    Each day's prediction is used to build the features for the next day's prediction.
    """
    feature_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 
                    'SMA_20', 'EMA_50', 'RSI', 'MACD', 'MACD_Signal', 
                    'BB_Upper', 'BB_Lower']
    
    forecasts = {model_name: [] for model_name in models.keys()}
    
    # We will generate forecasts for each model independently
    for model_name, model in models.items():
        # Copy history so models don't interfere with each other's simulated history
        sim_df = df_history.copy()
        
        # Determine last date in history
        last_date = sim_df['Date'].max()
        
        # Generate predictions day-by-day
        for step in range(horizon):
            # 1. Re-calculate indicators with latest data points
            sim_df = calculate_indicators(sim_df)
            
            # Get the very last row for current features (time t)
            current_row = sim_df.iloc[-1]
            
            # Predict Close(t+1)
            predicted_close = None
            
            if model_name in ['Linear Regression', 'Random Forest', 'XGBoost']:
                # ML logic
                scaler_x = scalers['ML']['scaler_x']
                scaler_y = scalers['ML']['scaler_y']
                
                # Reshape and scale features
                features = current_row[feature_cols].values.reshape(1, -1)
                features_scaled = scaler_x.transform(features)
                
                # Predict
                pred_scaled = model.predict(features_scaled)
                predicted_close = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0, 0]
                
            elif model_name == 'LSTM':
                # LSTM logic (needs last 60 days sequence)
                seq_len = 60
                if len(sim_df) < seq_len:
                    # Fallback to last Close if history is too short (should not happen)
                    predicted_close = current_row['Close']
                else:
                    scaler_x_lstm = scalers['LSTM']['scaler_x']
                    scaler_y_lstm = scalers['LSTM']['scaler_y']
                    
                    # Take last seq_len rows
                    seq_df = sim_df.iloc[-seq_len:]
                    
                    # Scale features
                    seq_scaled = scaler_x_lstm.transform(seq_df[feature_cols])
                    seq_scaled = seq_scaled.reshape(1, seq_len, len(feature_cols))
                    
                    # Predict
                    pred_scaled = model.predict(seq_scaled, verbose=0)
                    predicted_close = scaler_y_lstm.inverse_transform(pred_scaled)[0, 0]
            
            # Post-process prediction to avoid negative/implausible values
            predicted_close = max(0.01, predicted_close)
            forecasts[model_name].append(predicted_close)
            
            # Create next day's date (skip weekends)
            next_date = last_date + timedelta(days=1)
            while next_date.weekday() >= 5: # 5 is Saturday, 6 is Sunday
                next_date += timedelta(days=1)
            last_date = next_date
            
            # Estimate other values for the new day
            prev_close = current_row['Close']
            est_open = prev_close
            est_high = max(est_open, predicted_close) * 1.002
            est_low = min(est_open, predicted_close) * 0.998
            est_volume = sim_df['Volume'].iloc[-20:].mean() # Mean volume of last 20 days
            
            # Append new simulated row
            new_row = pd.DataFrame([{
                'Date': next_date,
                'Open': est_open,
                'High': est_high,
                'Low': est_low,
                'Close': predicted_close,
                'Volume': est_volume
            }])
            
            sim_df = pd.concat([sim_df, new_row], ignore_index=True)
            
    # Combine forecasts into a single DataFrame
    # Generate the business days list
    last_hist_date = df_history['Date'].max()
    future_dates = []
    curr_date = last_hist_date
    for _ in range(horizon):
        curr_date += timedelta(days=1)
        while curr_date.weekday() >= 5:
            curr_date += timedelta(days=1)
        future_dates.append(curr_date)
        
    forecast_df = pd.DataFrame({'Date': future_dates})
    for model_name, preds in forecasts.items():
        forecast_df[model_name] = preds
        
    return forecast_df
