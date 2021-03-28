from utils import * 

# Source environment file
load_dotenv()

# ============== #
# Rotation check #
# ============== #

# Retrieve prices for current 90 day period and prior 90 day period
# TODO refactor to make these cmd line arguments
tickers = 'QQQX TLT'
winners = []
for days in [0, 30]:
    current, prior = get_90_day_prices(tickers=tickers, lag_days=days)
    winner = calc_winner(current=current, prior=prior)
    winners.append(winner)

current_win, win_percent = winners[0]
prior_win, _ = winners[1]

send_alert = (current_win != prior_win)

# Send email notification of need to rebalance
if send_alert:
    
    RECIPIENT = os.environ.get('ADMIN')
    
    BODY_OF_MESSAGE = '''\
    Subject: [Investment Manager] Portfolio Rebalance Notification
        
    Over the previous 1-month period {0}'s 90-day growth performance beat {1}'s perfomance for {2} percent of the days compared. 
        
    The previous period's winner was {1}. You should reallocate your rotation bucket to 75% {0} - 25% {1}.
        
    Sincerely,
        Your automated investor algorithm.
    '''.format(current_win, prior_win, win_percent)
        
    send_email(to_addrs=RECIPIENT, email_text=BODY_OF_MESSAGE)
    
