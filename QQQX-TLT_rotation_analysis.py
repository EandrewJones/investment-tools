from utils import *

# ==================== #
# All history analysis #
# ==================== #

# Get entire price history
tickers = 'QQQX TLT'
all_history = yf.download(tickers, period='max')
all_history.dropna(inplace=True)

# Walk over 90 day periods and calculate growth rates
today = all_history.index.values[-1]
qqqx_gr = []
tlt_gr = []
dates = []
next_90_in_range = True
i = 0

while next_90_in_range:
    start = all_history.index.values[i]
    end = start + np.timedelta64(90, 'D')
    mask = (all_history.index.values >= start) & (all_history.index.values <= end)
    
    qqqx, tlt  = calc_growth(all_history.loc[mask])
    qqqx_gr.append(qqqx)
    tlt_gr.append(tlt)
    
    date = all_history.loc[mask].index.values[-1]
    dates.append(date)
    
    i += 1
    
    if date == today:
        next_90_in_range = False

# Convert to dataframe
d = {
    'period_end_date': dates,
    'QQQX': qqqx_gr,
    'TLT': tlt_gr
}
growth_rate_df = pd.DataFrame(data=d)
growth_rate_df.set_index('period_end_date', inplace=True)

# Calculate winner
growth_rate_df['winner'] = growth_rate_df.idxmax(axis=1)
monthly_counts = growth_rate_df.groupby(pd.Grouper(freq='M'))['winner'].value_counts(normalize=True, dropna=False).to_frame()

monthly_counts.columns = ['count']
monthly_counts.reset_index(level=[1], inplace=True)
monthly_counts_wide = monthly_counts.pivot(columns='winner')
monthly_counts_wide.fillna(0, inplace=True)
monthly_counts_wide.columns = monthly_counts_wide.columns.get_level_values(1)

monthly_counts_wide['winner'] = monthly_counts_wide.idxmax(axis=1)
monthly_counts_wide['win_pct'] = monthly_counts_wide.max(axis=1)


# Calculate Quantities of interest
monthly_counts_wide['lag'] = monthly_counts_wide['winner'].shift()
monthly_counts_wide.dropna(inplace=True)
monthly_counts_wide['rotate'] = (monthly_counts_wide['winner'] != monthly_counts_wide['lag'])

# 1. number of adjustments per year
monthly_counts_wide.groupby(pd.Grouper(freq='Y')).rotate.sum()

# 2. Total number of periods invested in each
monthly_counts_wide.winner.value_counts()