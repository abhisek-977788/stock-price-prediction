# AI & Machine Learning Stock Price Predictor Project Report

**Author:** AI & ML Research Intern  
**Date:** June 2026  
**Project Scope:** Implementation and Evaluation of Predictive Models for Financial Markets  

---

## 1. Executive Summary
The financial markets are characterized by volatility, complexity, and non-linearity. This project implements, compares, and evaluates multiple machine learning and deep learning methodologies to model and forecast stock prices. Using historical data from Yahoo Finance, we build technical indicators, extract sentiment from real-time news headlines, and deploy four prediction models: Linear Regression, Random Forest, XGBoost, and an LSTM (Long Short-Term Memory) Neural Network. 

By running automated evaluation metrics (MAE, MSE, RMSE, R²), the project provides an analytical comparison of traditional statistical models against ensemble learners and deep neural networks. Additionally, the dashboard integrates rule-based quantitative trading signals and natural language processing (NLP) to offer actionable buy/sell recommendations for investors.

---

## 2. Introduction & Literature Review
Stock price forecasting is one of the most challenging tasks in time-series analysis due to the Efficient Market Hypothesis (EMH), which states that asset prices reflect all available information. However, subsequent research in behavioral finance and quantitative trading suggests that micro-patterns, market momentum, and macroeconomic sentiment create exploitable inefficiencies.

This project focuses on two primary methodologies:
1. **Technical Analysis**: Utilizing historical price and volume data to compute statistical measures (Moving Averages, RSI, MACD, Bollinger Bands) that capture trend momentum and volatility.
2. **Sentiment Analysis**: Analyzing natural language signals from news headlines to capture short-term sentiment shifts that precede price movements.

---

## 3. Dataset & Data Engineering
We fetch real-time and historical daily stock data from the Yahoo Finance API (`yfinance`). The core features retrieved include:
- **Date**: The trading day.
- **Open Price**: The price at which the stock first traded.
- **Close Price**: The final price at which the stock traded during regular hours.
- **High Price**: The highest price reached during the day.
- **Low Price**: The lowest price reached during the day.
- **Volume**: The total number of shares traded.

### 3.1 Feature Engineering (Technical Indicators)
To enrich the features, we compute the following technical indicators:
- **Simple Moving Average (SMA-20)**:  
  $$SMA_{20} = \frac{1}{20} \sum_{i=0}^{19} Close_{t-i}$$
- **Exponential Moving Average (EMA-50)**:  
  $$EMA_{t} = Close_t \times \left(\frac{2}{50+1}\right) + EMA_{t-1} \times \left(1 - \frac{2}{50+1}\right)$$
- **Relative Strength Index (RSI-14)**:  
  A momentum oscillator that measures the speed and change of price movements between 0 and 100.
  $$RSI = 100 - \frac{100}{1 + RS}, \quad \text{where } RS = \frac{\text{Average Gain}}{\text{Average Loss}}$$
- **Moving Average Convergence Divergence (MACD)**:  
  The difference between the 12-day and 26-day EMAs, compared against a 9-day Signal Line.
- **Bollinger Bands**:  
  Volatility bands placed above and below a 20-day SMA, calculated using standard deviation:
  $$\text{Upper Band} = SMA_{20} + 2\sigma_{20}$$
  $$\text{Lower Band} = SMA_{20} - 2\sigma_{20}$$

---

## 4. Methodology & Machine Learning Models
We formulate the prediction problem as a supervised learning task: given historical features at day $t$, we predict the Close price at day $t+1$.

### 4.1 Linear Regression
Linear Regression serves as our baseline statistical model. It assumes a linear relationship between the input features and the target variable:
$$y = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \dots + \beta_k X_k + \epsilon$$

### 4.2 Random Forest Regressor
An ensemble learning method that fits multiple decision trees on bootstrap samples of the training data and averages their predictions to reduce variance and prevent overfitting.

### 4.3 XGBoost Regressor
Extreme Gradient Boosting (XGBoost) is an optimized distributed gradient boosting library. It sequentially trains decision trees, where each new tree corrects the errors of its predecessor, utilizing regularization to control complexity.

### 4.4 LSTM Neural Network (Deep Learning)
Long Short-Term Memory (LSTM) networks are a specialized type of Recurrent Neural Network (RNN) capable of learning long-term dependencies in sequential data. LSTM cells utilize gates (input, forget, output) to regulate the flow of information, mitigating the vanishing gradient problem in deep time-series networks.
We construct sequences of length 60 (past 60 trading days) to predict the next day's Close price.

---

## 5. Evaluation & Performance Metrics
To quantitatively evaluate model performance, we use four primary metrics:
- **Mean Absolute Error (MAE)**: Measures average magnitude of errors.
  $$MAE = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$$
- **Mean Squared Error (MSE)**: Penalizes larger errors heavily.
  $$MSE = \frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2$$
- **Root Mean Squared Error (RMSE)**: Expresses error in the original units.
  $$RMSE = \sqrt{MSE}$$
- **Coefficient of Determination ($R^2$ Score)**: Represents the proportion of variance explained by the model.
  $$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$

---

## 6. Sentiment Analysis & Decision Logic
For short-term qualitative evaluation, news articles are scraped from yfinance and processed using TextBlob NLP:
- **Polarity**: Measures the tone of the headline from -1 (extremely negative) to +1 (extremely positive).
- **Subjectivity**: Measures factual density vs. opinion bias (0 to 1).

### 6.1 Trading Signal Rules
- **RSI Strategy**: Buy if RSI < 30 (oversold); Sell if RSI > 70 (overbought).
- **MACD Strategy**: Buy when MACD crosses above its Signal Line; Sell when it crosses below.
- **Moving Average Strategy**: Buy when SMA-20 is above EMA-50; Sell when below.
The app combines these inputs into a final vote recommendation (Buy/Sell/Hold).

---

## 7. Conclusions & Future Scope
Ensemble techniques (XGBoost) and deep learning models (LSTM) capture temporal dynamics and volatility changes better than linear baselines, particularly during market regimes shifts. Future improvements include:
1. Incorporating order book depth and high-frequency order flows.
2. Training Transformer-based architectures (e.g., Temporal Fusion Transformers).
3. Implementing reinforcement learning agents to execute trades based on recommendations.
