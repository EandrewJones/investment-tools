import yfinance as yf, pandas as pd, numpy as np, datetime, os, time, glob, smtplib, ssl
from pandas import Series, DataFrame

# ================= #
# Utility functions #
# ================= #

# Function to calculate growth
def calc_growth(price_data, lag=0):
    """Uses first and last entry in yfinance data frame to 
    calculate period growth."""
    
    adj_close = price_data['Adj Close']
    growth_rate = 100 * (adj_close.iloc[-1,:] - adj_close.iloc[0, :]) / adj_close.iloc[0, :]
    return growth_rate


def to_ymd(date_time):
    """Converts numpy datetime64 to str format compatible with yfinance"""
    str_d = str(date_time)
    return pd.to_datetime(str_d).strftime('%Y-%m-%d')


def get_90_day_prices(tickers):
    """
    Retrieves previous 90 day stock prices for given stock tickers
    along wiht a 1-month lagged 90 day stock price.
    """
    # Get current period
    current_pd = yf.download(tickers, period='3mo')
    
    # Calculate lagged period start and end dates
    today = current_pd.index.values[-1]
    start, end = map(to_ymd, [today - np.timedelta64(days, 'D') for days in [120, 30]])
    priod_pd = yf.download(tickers, start=start, end=end)
    
    return current_pd, prior_pd


# ================= #
# Rotation analysis #
# ================= #


# Get current 3 month period and prior 3 month period
tickers = 'QQQ TLT'
current, prior = get_90_day_prices(tickers)

# Calculate growth
current_g, prior_g = map(calc_growth, [current, prior])

# Extract current and prior winners and compare
current_win = current_g.index.values[current_g.argmax()]
prior_win = prior_g.index.values[prior_g.argmax()]
send_alert = (current_win != prior_win)

# Send email notification of need to rebalance
if send_alert:
    # TODO write function that sends out email message via smtp   


#
# All history analysis
#

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
