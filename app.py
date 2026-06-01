import os
import sys
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Import helper libraries
import yfinance as yf

# Set up page configurations
st.set_page_config(
    page_title="AI & ML Stock Price Predictor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (CSS) for premium look and feel
st.markdown("""
<style>
    /* Global styles */
    .main {
        background-color: #f7f9fc;
        color: #2c3e50;
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0f2043 !important;
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] .stText {
        color: #b0bec5 !important;
    }
    section[data-testid="stSidebar"] label {
        color: #eceff1 !important;
        font-weight: 500;
    }
    
    /* Header decoration */
    .title-container {
        background: linear-gradient(135deg, #0f2043 0%, #1e3c72 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom cards */
    .metric-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 5px solid #2980b9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    
    .buy-signal {
        background-color: #e8f8f5;
        border-left: 5px solid #2ecc71;
        padding: 1.5rem;
        border-radius: 8px;
    }
    .sell-signal {
        background-color: #fdf2f2;
        border-left: 5px solid #e74c3c;
        padding: 1.5rem;
        border-radius: 8px;
    }
    .hold-signal {
        background-color: #fcfcfc;
        border-left: 5px solid #95a5a6;
        padding: 1.5rem;
        border-radius: 8px;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f1f2f6;
        border-radius: 4px 4px 0px 0px;
        padding-left: 20px;
        padding-right: 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e3c72 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Add utils to Python path to ensure clean imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import calculate_indicators, analyze_sentiment, generate_signals
from train_model import train_models
from predict import load_models_and_scalers, forecast_future_prices

# Define standard stock list
TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "NFLX", "META"]

# Header Title
st.markdown("""
<div class="title-container">
    <h1 style="margin: 0; font-size: 2.5rem;">📈 AI & Machine Learning Stock Price Predictor</h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
        Analyze historical data, evaluate predictive models, view sentiment context, and forecast future market trends.
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar configurations
st.sidebar.title("⚙️ Dashboard Controls")
selected_ticker = st.sidebar.selectbox("Select Ticker Symbol", TICKERS, index=0)

# Custom ticker option
custom_ticker = st.sidebar.text_input("Or Enter Custom Ticker (e.g. AMD, BABA):").strip().upper()
if custom_ticker:
    selected_ticker = custom_ticker

# Date period for historical data
period_options = {
    "1 Year": "1y",
    "2 Years": "2y",
    "5 Years": "5y",
    "10 Years": "10y"
}
selected_period_label = st.sidebar.selectbox("Historical Data Period", list(period_options.keys()), index=2)
selected_period = period_options[selected_period_label]

st.sidebar.markdown("---")
st.sidebar.markdown("**Deep Learning Configuration**")
lstm_epochs = st.sidebar.slider("LSTM Epochs", min_value=1, max_value=30, value=10)
lstm_batch_size = st.sidebar.selectbox("LSTM Batch Size", [16, 32, 64, 128], index=1)

# Helper function to fetch data and cache it
@st.cache_data(ttl=600)
def load_data(ticker, period):
    df = yf.download(ticker, period=period)
    if df.empty:
        return pd.DataFrame()
    # Flatten multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    df = df.reset_index()
    df = calculate_indicators(df)
    return df

# Fetch data
df = load_data(selected_ticker, selected_period)

if df.empty:
    st.error(f"⚠️ Failed to fetch data for ticker '{selected_ticker}'. Please verify the stock symbol.")
    st.stop()

# Get recent details
latest_price = df['Close'].iloc[-1]
price_diff = df['Close'].iloc[-1] - df['Close'].iloc[-2]
pct_diff = (price_diff / df['Close'].iloc[-2]) * 100

# Metric display
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.metric("Ticker Symbol", selected_ticker)
with m_col2:
    st.metric("Latest Close Price", f"${latest_price:.2f}")
with m_col3:
    st.metric("Daily Change ($)", f"${price_diff:.2f}", delta_color="normal")
with m_col4:
    st.metric("Daily Change (%)", f"{pct_diff:.2f}%")

# Main Tabs Setup
tabs = st.tabs([
    "🏠 Home Page", 
    "📊 Stock Data Analysis", 
    "🤖 Model Training", 
    "📈 Prediction Results", 
    "⚖️ Performance Comparison", 
    "🔮 Future Forecasting", 
    "💡 Conclusion & Insights"
])

# ----------------------------------------------------
# TAB 1: HOME PAGE
# ----------------------------------------------------
with tabs[0]:
    st.header("Project Overview")
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
        ### Objective
        This project builds and deploys an interactive AI/ML pipeline to analyze, visualize, and forecast stock prices. 
        It integrates standard statistical regression models with deep learning time-series architectures and sentiment NLP.

        ### Features
        - **Real-Time Data Ingestion**: Direct loading of tickers from Yahoo Finance API.
        - **Technical Analysis**: Visualizing indicators such as SMA, EMA, RSI, MACD, and Bollinger Bands.
        - **News Sentiment NLP**: Running polarity scoring on the latest headlines using TextBlob.
        - **Machine Learning & Deep Learning**: Running Linear Regression, Random Forest, XGBoost, and an LSTM Network.
        - **Recursive Forecasting**: Generating out-of-sample projections for 7, 15, and 30 business days.
        - **Automated Deliverables**: Generation of project report and PowerPoint slide deck.
        """)
        
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>💡 Guidelines & Usage</h4>
            <p>1. Select a ticker from the sidebar or enter a custom symbol.</p>
            <p>2. Review the historical data, indicators, and NLP sentiment.</p>
            <p>3. Train the machine learning models in the <b>Model Training</b> tab.</p>
            <p>4. Evaluate forecasting curves and download predictions as CSV files.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Action item
        st.info("👈 Use the controls on the left to set custom tickers and configuration parameters.")

# ----------------------------------------------------
# TAB 2: STOCK DATA ANALYSIS
# ----------------------------------------------------
with tabs[1]:
    st.header("📊 Technical Stock Analysis")
    
    # Selection of technical overlays
    st.markdown("##### Technical Indicator Chart Customization")
    c1, c2, c3, c4 = st.columns(4)
    show_ma = c1.checkbox("Show Moving Averages (SMA-20, EMA-50)", value=True)
    show_bb = c2.checkbox("Show Bollinger Bands", value=False)
    show_rsi = c3.checkbox("Show RSI Plot", value=False)
    show_macd = c4.checkbox("Show MACD Plot", value=False)

    # Candlestick chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="OHLC Price"
    ))

    if show_ma:
        if 'SMA_20' in df.columns:
            fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_20'], name='SMA 20', line=dict(color='orange', width=1.5)))
        if 'EMA_50' in df.columns:
            fig.add_trace(go.Scatter(x=df['Date'], y=df['EMA_50'], name='EMA 50', line=dict(color='blue', width=1.5)))
            
    if show_bb:
        if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
            fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_Upper'], name='BB Upper', line=dict(color='rgba(150, 150, 150, 0.4)', dash='dash')))
            fig.add_trace(go.Scatter(x=df['Date'], y=df['BB_Lower'], name='BB Lower', line=dict(color='rgba(150, 150, 150, 0.4)', dash='dash'), fill='tonexty'))

    fig.update_layout(
        title=f"{selected_ticker} Candlestick Price Chart",
        yaxis_title="Stock Price ($)",
        xaxis_title="Date",
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=40, r=40, t=40, b=40),
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Sub plots for RSI & MACD
    if show_rsi:
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI', line=dict(color='purple', width=1.5)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
        fig_rsi.update_layout(
            title="Relative Strength Index (RSI-14)",
            yaxis_title="Value",
            height=200,
            margin=dict(l=40, r=40, t=40, b=40),
            template="plotly_white"
        )
        st.plotly_chart(fig_rsi, use_container_width=True)

    if show_macd:
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD', line=dict(color='blue')))
        fig_macd.add_trace(go.Scatter(x=df['Date'], y=df['MACD_Signal'], name='Signal Line', line=dict(color='red', dash='dash')))
        fig_macd.add_trace(go.Bar(x=df['Date'], y=df['MACD_Hist'], name='Histogram', marker_color='gray'))
        fig_macd.update_layout(
            title="MACD (12, 26, 9)",
            yaxis_title="Value",
            height=200,
            margin=dict(l=40, r=40, t=40, b=40),
            template="plotly_white"
        )
        st.plotly_chart(fig_macd, use_container_width=True)

    # Historical raw data table
    with st.expander("View Raw Historical Data Table"):
        st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)

# ----------------------------------------------------
# TAB 3: MODEL TRAINING
# ----------------------------------------------------
with tabs[2]:
    st.header("🤖 Train AI & Machine Learning Models")
    st.markdown("""
    Train Linear Regression, Random Forest, XGBoost, and an LSTM Neural Network models for the selected ticker.
    The models will be optimized on the historical training set and saved dynamically.
    """)
    
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        st.write("##### Training Controls")
        if st.button("🚀 Train All Models", key="train_btn"):
            with st.spinner(f"Training models for {selected_ticker}... This can take a moment (especially for LSTM)."):
                try:
                    metrics = train_models(
                        ticker=selected_ticker,
                        period=selected_period,
                        lstm_epochs=lstm_epochs,
                        lstm_batch_size=lstm_batch_size
                    )
                    st.success("🎉 Models trained and saved successfully!")
                except Exception as e:
                    st.error(f"Error during model training: {e}")
                    
    with col_t2:
        st.write("##### Current Metric Standings")
        metrics_file = os.path.join('models', selected_ticker, 'metrics.json')
        if os.path.exists(metrics_file):
            import json
            with open(metrics_file, 'r') as f:
                saved_metrics = json.load(f)
            
            # Print metrics inside a table
            metrics_df = pd.DataFrame(saved_metrics).T
            st.dataframe(metrics_df.style.format(precision=4), use_container_width=True)
        else:
            st.warning("⚠️ No trained models detected for this ticker. Please click 'Train All Models' above to start training.")

# ----------------------------------------------------
# TAB 4: PREDICTION RESULTS
# ----------------------------------------------------
with tabs[3]:
    st.header("📈 Model Prediction Overlay")
    
    # Load models
    try:
        models, scalers = load_models_and_scalers(selected_ticker)
        
        # Predict on recent historical test data to show performance overlap
        # Let's get features
        feature_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 
                        'SMA_20', 'EMA_50', 'RSI', 'MACD', 'MACD_Signal', 
                        'BB_Upper', 'BB_Lower']
        
        test_df = df.iloc[-100:].copy() # Look at the last 100 days of history
        
        fig_pred = go.Figure()
        # Actual close
        fig_pred.add_trace(go.Scatter(x=test_df['Date'], y=test_df['Close'], name='Actual Price', line=dict(color='black', width=2)))
        
        # Check and load prediction scalers and run
        if 'ML' in scalers:
            scaler_x = scalers['ML']['scaler_x']
            scaler_y = scalers['ML']['scaler_y']
            
            X_test_scaled = scaler_x.transform(test_df[feature_cols])
            
            for m_name in ['Linear Regression', 'Random Forest', 'XGBoost']:
                if m_name in models:
                    preds_scaled = models[m_name].predict(X_test_scaled)
                    preds = scaler_y.inverse_transform(preds_scaled.reshape(-1, 1)).flatten()
                    
                    # Shift predicted points forward by 1 step because we train to predict Close(t+1)
                    pred_dates = test_df['Date'].shift(-1)
                    
                    fig_pred.add_trace(go.Scatter(x=pred_dates, y=preds, name=m_name, line=dict(dash='dash')))
                    
        if 'LSTM' in models and 'LSTM' in scalers:
            # We can run sequence predictions
            scaler_x_lstm = scalers['LSTM']['scaler_x']
            scaler_y_lstm = scalers['LSTM']['scaler_y']
            
            # Predict LSTM for the last 40 steps
            lstm_preds = []
            lstm_dates = []
            seq_len = 60
            
            for idx in range(len(df) - 40, len(df)):
                seq_df = df.iloc[idx - seq_len:idx]
                seq_scaled = scaler_x_lstm.transform(seq_df[feature_cols])
                seq_scaled = seq_scaled.reshape(1, seq_len, len(feature_cols))
                
                pred_sc = models['LSTM'].predict(seq_scaled, verbose=0)
                pred_val = scaler_y_lstm.inverse_transform(pred_sc)[0, 0]
                
                lstm_preds.append(pred_val)
                lstm_dates.append(df['Date'].iloc[idx])
                
            fig_pred.add_trace(go.Scatter(x=lstm_dates, y=lstm_preds, name='LSTM', line=dict(color='red', width=1.5)))

        fig_pred.update_layout(
            title="Comparison of Model Predictions vs Actual Prices (Recent History Overlay)",
            yaxis_title="Price ($)",
            xaxis_title="Date",
            height=550,
            template="plotly_white"
        )
        st.plotly_chart(fig_pred, use_container_width=True)
        
    except Exception as e:
        st.info("⚠️ Please train models first to see historical test predictions overlay.")

# ----------------------------------------------------
# TAB 5: PERFORMANCE COMPARISON
# ----------------------------------------------------
with tabs[4]:
    st.header("⚖️ Model Benchmark Comparison")
    
    metrics_file = os.path.join('models', selected_ticker, 'metrics.json')
    if os.path.exists(metrics_file):
        import json
        with open(metrics_file, 'r') as f:
            saved_metrics = json.load(f)
            
        m_df = pd.DataFrame(saved_metrics)
        
        # Display metrics side by side
        col_m1, col_m2 = st.columns(2)
        
        with col_m1:
            st.write("##### Root Mean Squared Error (RMSE) - Lower is Better")
            fig_rmse = px.bar(m_df.loc['RMSE'], labels={'value': 'RMSE', 'index': 'Model'}, color=m_df.columns)
            st.plotly_chart(fig_rmse, use_container_width=True)
            
        with col_m2:
            st.write("##### R-Squared Score (R²) - Higher is Better")
            fig_r2 = px.bar(m_df.loc['R2'], labels={'value': 'R2 Score', 'index': 'Model'}, color=m_df.columns)
            st.plotly_chart(fig_r2, use_container_width=True)
            
        # Metric Table
        st.write("##### Detailed Evaluation Metrics")
        st.dataframe(m_df.T.style.format(precision=4), use_container_width=True)
    else:
        st.warning("⚠️ No trained models detected. Please train models first to display benchmark metrics.")

# ----------------------------------------------------
# TAB 6: FUTURE FORECASTING
# ----------------------------------------------------
with tabs[5]:
    st.header("🔮 Multi-Day Future Forecasting")
    
    forecast_horizon = st.selectbox("Select Forecast Horizon (Days)", [7, 15, 30], index=2)
    
    if st.button("🔮 Forecast Future Prices", key="forecast_btn"):
        try:
            models, scalers = load_models_and_scalers(selected_ticker)
            
            # Predict future prices
            forecast_df = forecast_future_prices(df, models, scalers, selected_ticker, horizon=forecast_horizon)
            
            # Chart plotting
            fig_forecast = go.Figure()
            
            # Plot historical prices (last 60 days)
            hist_plot = df.iloc[-60:]
            fig_forecast.add_trace(go.Scatter(x=hist_plot['Date'], y=hist_plot['Close'], name='Historical Price', line=dict(color='black', width=2)))
            
            # Plot forecasts
            for col in forecast_df.columns:
                if col != 'Date':
                    # Prepend the last historical close so predictions link seamlessly to history
                    last_hist_row = pd.DataFrame([{
                        'Date': hist_plot['Date'].iloc[-1],
                        col: hist_plot['Close'].iloc[-1]
                    }])
                    link_df = pd.concat([last_hist_row, forecast_df[['Date', col]]], ignore_index=True)
                    
                    fig_forecast.add_trace(go.Scatter(x=link_df['Date'], y=link_df[col], name=f'{col} Forecast', line=dict(dash='dash', width=2)))
            
            fig_forecast.update_layout(
                title=f"{selected_ticker} Future Price Forecast (Next {forecast_horizon} Days)",
                yaxis_title="Price ($)",
                xaxis_title="Date",
                height=550,
                template="plotly_white"
            )
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # Output dataframe and download button
            st.write("##### Predicted Prices Table")
            st.dataframe(forecast_df.style.format(precision=2), use_container_width=True)
            
            csv = forecast_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Predictions as CSV",
                data=csv,
                file_name=f"{selected_ticker}_predictions_{forecast_horizon}_days.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error forecasting future prices: {e}")
            st.info("Make sure models have been trained for this ticker.")

# ----------------------------------------------------
# TAB 7: CONCLUSION & INSIGHTS (Advanced Features)
# ----------------------------------------------------
with tabs[6]:
    st.header("💡 Market Insights, Sentiment & Signals")
    
    col_ins1, col_ins2 = st.columns([1, 1])
    
    with col_ins1:
        st.write("##### 📰 Real-Time News & Sentiment Analysis")
        with st.spinner("Analyzing recent stock news..."):
            news_items = analyze_sentiment(selected_ticker)
            
        if news_items:
            for item in news_items:
                sentiment_color = "#2ecc71" if item['sentiment'] == 'Positive' else ("#e74c3c" if item['sentiment'] == 'Negative' else "#95a5a6")
                st.markdown(f"""
                <div style="background-color: white; padding: 10px; border-radius: 5px; margin-bottom: 8px; border-left: 4px solid {sentiment_color}; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <p style="margin: 0; font-size: 0.95rem; font-weight: bold;"><a href="{item['link']}" target="_blank" style="text-decoration: none; color: #2c3e50;">{item['title']}</a></p>
                    <p style="margin: 3px 0 0 0; font-size: 0.8rem; color: #7f8c8d;">
                        Publisher: {item['publisher']} | Time: {item['time']}
                    </p>
                    <p style="margin: 3px 0 0 0; font-size: 0.8rem; font-weight: 500;">
                        Sentiment: <span style="color: {sentiment_color};">{item['sentiment']}</span> (Polarity: {item['polarity']})
                    </p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent news found or error scraping yfinance feeds.")

    with col_ins2:
        st.write("##### 🚥 Buy/Sell Signal Indicators")
        
        # Run signal engine
        signal_df = generate_signals(df)
        if not signal_df.empty:
            latest_sig = signal_df.iloc[-1]
            rec_action = latest_sig['Action']
            score = latest_sig['Score']
            
            rec_class = "buy-signal" if rec_action == "Buy" else ("sell-signal" if rec_action == "Sell" else "hold-signal")
            
            st.markdown(f"""
            <div class="{rec_class}">
                <h3 style="margin: 0; color: #2c3e50;">Recommendation: {rec_action}</h3>
                <p style="margin: 5px 0 0 0; font-size: 1rem; color: #34495e;">Signal Consensus Score: <b>{score}</b> (Range: -3 to +3)</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Individual Technical Indicator Statuses
            st.write("\n##### Strategy Component Summary")
            
            sig_rsi = latest_sig['Signal_RSI']
            sig_macd = latest_sig['Signal_MACD']
            sig_ma = latest_sig['Signal_MA']
            
            # Print indicator statuses
            def color_label(val):
                if val == 'Buy':
                    return f'<span style="color: #2ecc71; font-weight: bold;">Buy</span>'
                elif val == 'Sell':
                    return f'<span style="color: #e74c3c; font-weight: bold;">Sell</span>'
                return f'<span style="color: #95a5a6; font-weight: bold;">Hold</span>'

            st.markdown(f"""
            - **RSI (14-period)**: current value is `{latest_sig['RSI']:.2f}` → {color_label(sig_rsi)}
            - **MACD / Signal Crossover**: line value `{latest_sig['MACD']:.2f}`, signal `{latest_sig['MACD_Signal']:.2f}` → {color_label(sig_macd)}
            - **Moving Average Alignment**: SMA-20 `{latest_sig['SMA_20']:.2f}` vs EMA-50 `{latest_sig['EMA_50']:.2f}` → {color_label(sig_ma)}
            """, unsafe_allow_html=True)
        else:
            st.info("Not enough historical data points to generate indicators and signals.")

    # ----------------------------------------------------
    # REPORTS DOWNLOAD SECTION
    # ----------------------------------------------------
    st.markdown("---")
    st.write("##### 📄 Generate & Download Reports")
    
    rep_col1, rep_col2 = st.columns(2)
    
    with rep_col1:
        if st.button("📁 Compile Deliverables Report & Slides", key="gen_artifacts_btn"):
            with st.spinner("Generating project documents..."):
                try:
                    from generate_artifacts import create_report, create_presentation
                    create_report()
                    create_presentation()
                    st.success("Artifacts created successfully! You can download them below.")
                except Exception as e:
                    st.error(f"Error compiling artifacts: {e}")
                    
    with rep_col2:
        report_path = 'reports/project_report.md'
        pptx_path = 'reports/presentation.pptx'
        
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                rep_data = f.read()
            st.download_button(
                label="📥 Download Internship Project Report (Markdown)",
                data=rep_data,
                file_name="Internship_Project_Report.md",
                mime="text/markdown"
            )
            
        if os.path.exists(pptx_path):
            with open(pptx_path, 'rb') as f:
                pptx_data = f.read()
            st.download_button(
                label="📥 Download PowerPoint Slide Deck (PPTX)",
                data=pptx_data,
                file_name="Internship_Presentation.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
