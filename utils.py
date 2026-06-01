import pandas as pd
import numpy as np
from textblob import TextBlob
import yfinance as yf

def calculate_indicators(df):
    """
    Calculate technical indicators for stock data:
    - Moving Averages (SMA, EMA)
    - Relative Strength Index (RSI)
    - MACD and Signal line
    - Bollinger Bands
    """
    # Make a copy to avoid modifications to original
    df = df.copy()

    # 1. Moving Averages
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()

    # 2. Relative Strength Index (RSI)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    # 3. MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # 4. Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (2 * df['BB_Std'])
    df['BB_Lower'] = df['BB_Middle'] - (2 * df['BB_Std'])

    return df

def analyze_sentiment(ticker_symbol):
    """
    Fetch recent news articles for the ticker and analyze their sentiment.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        news = ticker.news
        if not news:
            return []
    except Exception as e:
        print(f"Error fetching news for {ticker_symbol}: {e}")
        return []

    sentiment_results = []
    for article in news[:8]:  # Get top 8 news items
        title = article.get('title', '')
        publisher = article.get('publisher', '')
        link = article.get('link', '')
        provider_publish_time = article.get('providerPublishTime', 0)
        
        # Sentiment Analysis
        blob = TextBlob(title)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        if polarity > 0.05:
            sentiment = 'Positive'
        elif polarity < -0.05:
            sentiment = 'Negative'
        else:
            sentiment = 'Neutral'
            
        sentiment_results.append({
            'title': title,
            'publisher': publisher,
            'link': link,
            'time': pd.to_datetime(provider_publish_time, unit='s').strftime('%Y-%m-%d %H:%M'),
            'polarity': round(polarity, 2),
            'subjectivity': round(subjectivity, 2),
            'sentiment': sentiment
        })
        
    return sentiment_results

def generate_signals(df):
    """
    Generate Buy/Sell/Hold signals based on RSI, MACD, and MA Crossover.
    """
    if df.empty or len(df) < 50:
        return df

    df = df.copy()
    
    # Initialize signal columns
    df['Signal_RSI'] = 'Hold'
    df['Signal_MACD'] = 'Hold'
    df['Signal_MA'] = 'Hold'
    df['Action'] = 'Hold'
    df['Score'] = 0

    # 1. RSI Signals
    df.loc[df['RSI'] < 30, 'Signal_RSI'] = 'Buy'
    df.loc[df['RSI'] > 70, 'Signal_RSI'] = 'Sell'

    # 2. MACD Signals (Crossovers)
    # Buy when MACD crosses above Signal line, Sell when it crosses below
    macd_cross_up = (df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))
    macd_cross_down = (df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))
    df.loc[macd_cross_up, 'Signal_MACD'] = 'Buy'
    df.loc[macd_cross_down, 'Signal_MACD'] = 'Sell'

    # 3. Moving Average Signals (Golden/Death Crossover or price relative to EMA)
    ma_cross_up = (df['SMA_20'] > df['EMA_50']) & (df['SMA_20'].shift(1) <= df['EMA_50'].shift(1))
    ma_cross_down = (df['SMA_20'] < df['EMA_50']) & (df['SMA_20'].shift(1) >= df['EMA_50'].shift(1))
    df.loc[ma_cross_up, 'Signal_MA'] = 'Buy'
    df.loc[ma_cross_down, 'Signal_MA'] = 'Sell'

    # 4. Score Calculation for Final Action
    # Buy scores: +1, Sell scores: -1
    for col in ['Signal_RSI', 'Signal_MACD', 'Signal_MA']:
        df.loc[df[col] == 'Buy', 'Score'] += 1
        df.loc[df[col] == 'Sell', 'Score'] -= 1

    # Final Combined Recommendation
    df.loc[df['Score'] >= 1, 'Action'] = 'Buy'
    df.loc[df['Score'] <= -1, 'Action'] = 'Sell'
    df.loc[df['Score'] == 0, 'Action'] = 'Hold'

    return df
