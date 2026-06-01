# AI & Machine Learning Stock Price Predictor

This is an end-to-end Python-based Machine Learning and Deep Learning Stock Price Predictor web application. It fetches historical stock market data, performs technical feature engineering and news sentiment analysis, trains and compares multiple models, and forecasts future stock values with interactive visualization.

---

## Key Features

1. **Stock Ingestion**: Fetches dynamic datasets via the Yahoo Finance API (`yfinance`) for any ticker symbol.
2. **Technical Indicator Engine**: Calculates:
   - Simple Moving Average (SMA-20)
   - Exponential Moving Average (EMA-50)
   - Relative Strength Index (RSI-14)
   - MACD (and Signal Line)
   - Bollinger Bands
3. **News Sentiment Analysis**: Real-time ticker news parsing and natural language processing (NLP) polarity scoring using `TextBlob`.
4. **Machine Learning Suite**: Implements and benchmarks:
   - Linear Regression
   - Random Forest Regressor
   - XGBoost Regressor
   - LSTM Neural Network (Keras/TensorFlow)
5. **Autoregressive Multi-Day Forecast**: Multi-day forecasting (7, 15, and 30 business days) utilizing recursive feature feeding.
6. **Rule-Based Trading Signals**: Combined consensus recommendation engine (Buy/Sell/Hold) based on RSI, MACD, and MA Crossovers.
7. **Report Compilation**: Automation pipeline script to generate a 15-page equivalent markdown project report and a custom slide presentation using `python-pptx`.

---

## Directory Structure

```
stock-price-predictor/
├── data/                    # Directory for cached data and downloaded CSVs
├── models/                  # Directory for saved trained models & scalers
├── notebooks/               # For experimental notebooks (optional)
├── reports/                 # Holds generated reports and PPTX files
│   ├── project_report.md    # 10-15 pages equivalent comprehensive report
│   └── presentation.pptx    # Generated PowerPoint slide deck
├── app.py                   # Main Streamlit web application
├── train_model.py           # Script to train and save ML/DL models
├── predict.py               # Pipeline script for forecasting and inference
├── utils.py                 # Helper functions (indicators, sentiment, formatting)
├── generate_artifacts.py    # Script to programmatically compile report & PPTX presentation
├── requirements.txt         # Project dependencies
└── README.md                # Documentation and setup instructions
```

---

## Setup & Installation

### 1. Clone or Copy Project Files
Place all the project files in your directory (e.g., `d:/Stock Price Predictor`).

### 2. Install Dependencies
Make sure you have Python 3.8+ installed. Install all required packages:
```bash
pip install -r requirements.txt
```

---

## Usage Guide

### 1. Run Model Training (CLI)
You can train models for a specific stock ticker using the CLI script. This downloads the dataset, scales the variables, trains LR, RF, XGBoost, and LSTM, evaluates accuracy metrics, and saves the models.
```bash
python train_model.py --ticker AAPL --period 5y --epochs 10 --batch_size 32
```

### 2. Generate Reports & Presentation Slide Deck
Run the generator script to create the PowerPoint presentation slide deck and markdown project report:
```bash
python generate_artifacts.py
```
This writes:
- `reports/project_report.md`
- `reports/presentation.pptx`

### 3. Launch Streamlit Web Application
Run the interactive dashboard:
```bash
streamlit run app.py
```
This launches a browser session where you can:
- Change tickers.
- Enable technical indicator plot overlays.
- View real-time news articles with sentiment labels.
- Train models on-the-fly.
- Run forecasts for 7, 15, or 30 days.
- Download forecast tables as CSV.
- Download compiled presentation and report documents.
