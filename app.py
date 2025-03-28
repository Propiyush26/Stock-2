from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import yfinance as yf
import pandas as pd
import talib
import plotly.graph_objs as go
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Mock User Database (Replace with SQLAlchemy/PostgreSQL)
users = {'user1': {'password': 'pass1'}}

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        user = User()
        user.id = user_id
        return user
    return None

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    ticker = request.form['ticker']
    stock = yf.Ticker(ticker)
    info = stock.info
    history = stock.history(period="1y")
    
    # Calculate Technical Indicators
    closes = history['Close'].values
    history['SMA_50'] = talib.SMA(closes, timeperiod=50)
    history['RSI'] = talib.RSI(closes, timeperiod=14)
    
    # Generate Plotly Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=history.index,
        open=history['Open'],
        high=history['High'],
        low=history['Low'],
        close=history['Close'],
        name='Price'
    ))
    fig.add_trace(go.Scatter(
        x=history.index,
        y=history['SMA_50'],
        name='SMA 50',
        line=dict(color='blue')
    ))
    fig.update_layout(title=f"{ticker} Stock Analysis")
    chart = fig.to_html(full_html=False)
    
    # Fetch News
    newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
    news = newsapi.get_everything(q=ticker, language='en', sort_by='publishedAt')['articles'][:5]
    
    return render_template('analysis.html', 
        ticker=ticker,
        data={
            'name': info.get('longName', ticker),
            'price': info.get('currentPrice', 'N/A'),
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'market_cap': info.get('marketCap', 'N/A'),
            'chart': chart,
            'news': news
        }
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User()
            user.id = username
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)