from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from tradier_api import TradierAPI
import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'your_super_secret_key_here_please_change_this_seriously' # IMPORTANT: Change this to a strong, random key!

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # The view function for login

# Dummy User class (for demonstration only - in a real app, use a database)
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password # In real apps, store hashed passwords

    def get_id(self):
        return str(self.id)

# Hardcoded users for demonstration
# In a real application, fetch from a database and use hashed passwords
USERS = {
    "demo": User(1, "demo", "password123"),
    "trader": User(2, "trader", "securepassword")
}

@login_manager.user_loader
def load_user(user_id):
    """
    Given 'user_id', return the User object.
    """
    for user in USERS.values():
        if user.id == int(user_id):
            return user
    return None

tradier_api = TradierAPI()

# Dummy account ID for testing (replace with actual account ID or dynamic lookup)
TRADIER_ACCOUNT_ID = "VA65088995" # <<< REPLACE WITH YOUR TRADIER ACCOUNT ID HERE >>>

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = USERS.get(username)
        if user and user.password == password: # In real app: check hashed password
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required # Protect this route
def index():
    # Fetch some default market data or portfolio overview
    symbols = ['SPY', 'AAPL', 'MSFT', 'GOOGL']
    quotes_data = tradier_api.get_quotes(symbols)
    quotes = quotes_data['quotes']['quote'] if quotes_data and 'quotes' in quotes_data and quotes_data['quotes'] else []

    # Fetch account balances
    balances_data = tradier_api.get_balances(TRADIER_ACCOUNT_ID)
    balances = balances_data['balances'] if balances_data and 'balances' in balances_data else {}

    # Fetch positions
    positions_data = tradier_api.get_positions(TRADIER_ACCOUNT_ID)
    positions = positions_data['positions']['position'] if positions_data and 'positions' in positions_data and positions_data['positions'] else []

    return render_template('index.html',
                           quotes=quotes,
                           balances=balances,
                           positions=positions,
                           current_user=current_user) # Pass current_user to template

@app.route('/market_data', methods=['GET', 'POST'])
@login_required # Protect this route
def market_data():
    symbol_to_fetch = ''
    quotes = None
    historical_data = None
    option_chain = None
    expirations = None

    if request.method == 'POST':
        symbol_to_fetch = request.form.get('symbol').upper()
        data_type = request.form.get('data_type')

        if symbol_to_fetch:
            if data_type == 'quote':
                quotes_data = tradier_api.get_quotes(symbol_to_fetch)
                quotes = quotes_data['quotes']['quote'] if quotes_data and 'quotes' in quotes_data else []
                if quotes and not isinstance(quotes, list): # Handle single quote vs list
                    quotes = [quotes]
            elif data_type == 'history':
                end_date = datetime.date.today().strftime('%Y-%m-%d')
                start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime('%Y-%m-%d') # Last 1 year
                history_data = tradier_api.get_history(symbol_to_fetch, start=start_date, end=end_date)
                historical_data = history_data['history']['day'] if history_data and 'history' in history_data else []
            elif data_type == 'options':
                # First, get available expirations
                expirations_data = tradier_api.get_option_chains(symbol_to_fetch, expiration=None) # Pass None to get all expirations
                if expirations_data and 'expirations' in expirations_data and expirations_data['expirations']:
                    expirations = expirations_data['expirations']['date']
                    if expirations and not isinstance(expirations, list):
                        expirations = [expirations] # Ensure it's a list
                    # Fetch chain for the first available expiration by default
                    if expirations:
                        selected_expiration = request.form.get('expiration', expirations[0])
                        option_chain_data = tradier_api.get_option_chains(symbol_to_fetch, selected_expiration)
                        option_chain = option_chain_data['options']['option'] if option_chain_data and 'options' in option_chain_data else []
                else:
                    flash(f"No option expirations found for {symbol_to_fetch}", 'warning')

    return render_template('market_data.html',
                           symbol=symbol_to_fetch,
                           quotes=quotes,
                           historical_data=historical_data,
                           option_chain=option_chain,
                           expirations=expirations)

@app.route('/trade', methods=['GET', 'POST'])
@login_required # Protect this route
def trade():
    if request.method == 'POST':
        symbol = request.form.get('symbol').upper()
        side = request.form.get('side') # buy, sell, buy_to_cover, sell_short, etc.
        quantity = int(request.form.get('quantity'))
        order_type = request.form.get('order_type') # market, limit, stop, stop_limit
        duration = request.form.get('duration') # day, gtc
        price = request.form.get('price') # For limit/stop orders
        option_symbol = request.form.get('option_symbol') # For option orders
        order_class = request.form.get('order_class') # equity, option, multileg

        order_data = {
            'class': order_class,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'type': order_type,
            'duration': duration,
        }

        if order_type in ['limit', 'stop', 'stop_limit'] and price:
            order_data['price'] = float(price)

        if order_class == 'option' and option_symbol:
            order_data['option_symbol'] = option_symbol

        # You might want to add a preview step before placing the actual order
        # For simplicity, we'll place it directly here.
        result = tradier_api.place_order(TRADIER_ACCOUNT_ID, order_data)

        if result and 'order' in result and result['order']['status'] == 'ok':
            flash(f"Order for {quantity} {symbol} ({side} {order_type}) placed successfully!", 'success')
        elif result and 'errors' in result:
            error_msg = result['errors']['error']
            if isinstance(error_msg, list):
                error_msg = ', '.join(error_msg)
            flash(f"Error placing order: {error_msg}", 'danger')
        else:
            flash("An unknown error occurred while placing the order.", 'danger')

        return redirect(url_for('trade'))

    return render_template('trade.html')

@app.route('/portfolio')
@login_required # Protect this route
def portfolio():
    # Fetch account balances
    balances_data = tradier_api.get_balances(TRADIER_ACCOUNT_ID)
    balances = balances_data['balances'] if balances_data and 'balances' in balances_data else {}

    # Fetch positions
    positions_data = tradier_api.get_positions(TRADIER_ACCOUNT_ID)
    positions = positions_data['positions']['position'] if positions_data and 'positions' in positions_data else []

    # Fetch order history
    orders_data = tradier_api.get_orders(TRADIER_ACCOUNT_ID)
    orders = orders_data['orders']['order'] if orders_data and 'orders' in orders_data else []

    return render_template('portfolio.html',
                           balances=balances,
                           positions=positions,
                           orders=orders)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)