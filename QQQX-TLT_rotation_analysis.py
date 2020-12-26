from utils import *

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
