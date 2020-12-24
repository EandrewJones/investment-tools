import yfinance as yf, pandas as pd, numpy as np, datetime, os, time, glob, smtplib, ssl
from pandas import Series, DataFrame

# ================= #
# Utility functions #
# ================= #

# Function to calculate growth
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


# ============== #
# Rotation check #
# ============== #


# Retrieve prices for current 90 day period and prior 90 day period
tickers = 'QQQX TLT'
winners = []
for days in [0, 30]:
    current, prior = get_90_day_prices(tickers=tickers, lag_days=days)
    winner = calc_winner(current=current, prior=prior)
    winners.append(winner)

current_win, _ = winners[0]
prior_win, _ = winners[1]

send_alert = (current_win != prior_win)

# Send email notification of need to rebalance
if send_alert:
    # TODO write function that sends out email message via smtp   


# ==================== #
# All history analysis #
# ==================== #

tickers = 'QQQX TLT'
all_history = yf.download(tickers, period='max')
all_history.dropna(inplace=True)
today = all_history.index.values[-1]

winners = []
periods = []
next_90_in_range = True

while next_90_in_range:
    p90, p30  = [today - np.timedelta64(days, 'D') for days in [90, 30]]
    mask = (all_history.index.values > p90) & (all_history.index.values <= today)

    # Calculate winner and add to df
    growth = calc_growth(all_history.loc[mask])
    winner = growth.index.values[growth.argmax()]
    winners.append(winner)
    periods.append(today)

    # Update params
    today = p30
    next_90 = today - np.timedelta64(90, 'D')
    next_90_in_range = (np.sum(all_history.index.values <= next_90) > 0)


# Create dataframe
d = {
    'period_end_date': periods,
    'winner': winners
    }
winner_df = pd.DataFrame(data=d).sort_values(by='period_end_date')

# Create rotation boolean
winner_df['lag'] = winner_df['winner'].shift()
winner_df['rotate'] = (winner_df['winner'] != winner_df['lag'])
winner_df.drop(166, inplace=True)

# Calculate quantities of interest
rotations_year = winner_df.set_index('period_end_date').groupby(pd.Grouper(freq='Y'))['rotate'].sum()
winner_count = winner_df.winner.value_counts()

winner_count
rotations_year
