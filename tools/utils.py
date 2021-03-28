import yfinance as yf, pandas as pd, numpy as np, datetime, os, time, smtplib, ssl
from pandas import Series, DataFrame
from dotenv import load_dotenv

# ================= #
# Utility functions #
# ================= #

def calc_growth(price_data):
    """Uses first and last entry in yfinance data frame to 
    calculate period growth."""
    
    adj_close = price_data['Adj Close']
    growth_rate = 100 * (adj_close.iloc[-1,:] - adj_close.iloc[0, :]) / adj_close.iloc[0, :]
    return growth_rate


def to_ymd(date_time):
    """Converts numpy datetime64 to str format compatible with yfinance"""
    str_d = str(date_time)
    return pd.to_datetime(str_d).strftime('%Y-%m-%d')


def get_90_day_prices(tickers, lag_days=0):
    """
    Retrieves previous 90 day stock prices for given stock tickers
    along wiht a 1-month lagged 90 day stock price.
    """
    today = datetime.date.today()
    
    # Get current period
    end = np.datetime64(today) - np.timedelta64(lag_days, 'D')
    start = end - np.timedelta64(90, 'D')
    current_pd = yf.download(tickers, start=to_ymd(start), end=to_ymd(end))
    
    # Get previous period
    end = end - np.timedelta64(30, 'D')
    start = end - np.timedelta64(90, 'D')
    prior_pd = yf.download(tickers, start=to_ymd(start), end=to_ymd(end))
    
    return current_pd, prior_pd


def calc_winner(current, prior):
    """
    Takes previous 90 day prices and 1-month lagged 90 day prices and
    returns which index won during that period based on the daily winner.
    Also returns entropy as a measure of certainity.
    """
    
    # Match 90 day windows from each period
    mask = (current.index.values > prior.index.values[-1])
    end = current.loc[mask]['Adj Close']
    start = prior.iloc[0:sum(mask), ]['Adj Close']
    
    # Calculate growth
    change = np.subtract(end, start)
    growth = np.true_divide(change, start)
    
    # Get winner
    win_idx = np.array(growth).argmax(axis=1)
    counts = pd.Series(growth.columns[win_idx]).value_counts(normalize=True)
    winner = counts.index.values[counts.argmax()]
    win_pct = counts.round(decimals=3).max() * 100
    
    return winner, win_pct


def send_email(to_addrs, email_text):
    """
    Sends email with given header and body to specified email address.
    """
    # Source environment file
    load_dotenv()
    
    # Get server info
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    try:
        if MAIL_SERVER is None:
            print('MAIL_SERVER not defined in environment file.')
        if MAIL_USERNAME is None:
            print('MAIL_USERNAME not defined in environment file.')
        if MAIL_PASSWORD is None:
            print('MAIL_PASSWORD not defined in environment file.')
    except NameError:
        print('Server credentials not specified.')
    
    # Instantiate server and send message
    context = ssl.create_default_context()
    
    with smtplib.SMTP(host=MAIL_SERVER, port=MAIL_PORT) as server:
        server.starttls(context=context)
        server.login(user=MAIL_USERNAME, password=MAIL_PASSWORD)
        server.sendmail(from_addr=MAIL_USERNAME, to_addrs=to_addrs, msg=email_text)