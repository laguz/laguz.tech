import cachetools.func
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from urllib.parse import urlparse, urljoin
import concurrent.futures

import requests
import cachetools.func
from uvatradier import Tradier, Account, Quotes, OptionsData, EquityOrder, OptionsOrder
from config import Config
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=[])

# MongoDB setup
client = MongoClient(app.config['MONGO_URI'])
db = client.get_database("tradingbot") # Gets the database specified in MONGO_URI
users_collection = db.users
trades_collection = db.trades
pnl_collection = db.pnl_history # To store daily/periodic P&L snapshots

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redirect to login page if not authenticated
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'

# Tradier API setup
tradier_account_id = app.config['TRADIER_ACCOUNT_ID']
tradier_access_token = app.config['TRADIER_ACCESS_TOKEN']
tradier_live_trading = app.config['TRADIER_LIVE_TRADING']

# Instantiate Tradier classes
# Note: For production, ensure live_trade=True if you intend to place live trades.
# For development/testing, keep live_trade=False or use the Tradier sandbox API.
tradier_api_base = Tradier(tradier_account_id, tradier_access_token, live_trade=tradier_live_trading)
tradier_account = Account(tradier_account_id, tradier_access_token, live_trade=tradier_live_trading)
tradier_quotes = Quotes(tradier_account_id, tradier_access_token, live_trade=tradier_live_trading)
tradier_options_data = OptionsData(tradier_account_id, tradier_access_token, live_trade=tradier_live_trading)
tradier_equity_order = EquityOrder(tradier_account_id, tradier_access_token, live_trade=tradier_live_trading)
tradier_options_order = OptionsOrder(tradier_account_id, tradier_access_token, live_trade=tradier_live_trading)


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.password_hash = user_data['password']
        self.tradier_account_id = user_data.get('tradier_account_id')
        self.tradier_access_token = user_data.get('tradier_access_token')

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    target_clean = target.strip().replace('\\', '/')
    if target_clean.startswith('//'):
        return False
    test_url = urlparse(urljoin(request.host_url, target_clean))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def handle_route_exception(e, route_name):
    if isinstance(e, requests.exceptions.RequestException):
        msg = f"Error connecting to Tradier API: {e}" if route_name == 'dashboard' else f"Error communicating with Tradier API: {e}"
        flash(msg, 'danger')
    else:
        app.logger.exception(f"An unexpected error occurred {'in dashboard' if route_name == 'dashboard' else 'during trade'}")
        msg = f"An unexpected error occurred: {e}" if route_name == 'dashboard' else f"An error occurred: {e}"
        flash(msg, 'danger')

# --- Routes ---

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = users_collection.find_one({'username': username})

        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('dashboard')
            return redirect(next_page)
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html', username=username)

        existing_user = users_collection.find_one({'$or': [{'username': username}, {'email': email}]}, {'username': 1, 'email': 1})
        if existing_user:
            if existing_user.get('username') == username:
                flash('Username already exists. Please choose a different one.', 'warning')
                return render_template('register.html', username=username)
            if existing_user.get('email') == email:
                flash('Email already exists. Please choose a different one.', 'warning')
                return render_template('register.html', email=email)

        hashed_password = generate_password_hash(password)
        users_collection.insert_one({'username': username, 'email': email, 'password': hashed_password})
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get account balances and positions from Tradier concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_balance = executor.submit(tradier_account.get_account_balance)
            future_positions = executor.submit(tradier_account.get_positions)
            future_gain_loss = executor.submit(tradier_account.get_gainloss)

            account_balance = future_balance.result()
            positions = future_positions.result()
            gain_loss = future_gain_loss.result()

        # Calculate P&L (simplified - you'll want to store this more robustly)
        total_equity = account_balance.get('total_equity', 0)
        total_market_value = account_balance.get('total_market_value', 0)
        pnl_today = account_balance.get('realized_day_gain_loss', 0) + account_balance.get('unrealized_day_gain_loss', 0) # Example of combining
        pnl_total = account_balance.get('realized_gain_loss', 0) + account_balance.get('unrealized_gain_loss', 0) # Example of combining

        # Fetch recent trades from your MongoDB (up to N trades)
        recent_trades = trades_collection.find({'user_id': current_user.id}).sort('timestamp', -1).limit(10)

        # Fetch P&L history from your MongoDB (limit to last 100 entries)
        pnl_history_data = list(pnl_collection.find({'user_id': current_user.id}).sort('date', -1).limit(100))
        pnl_history_data.reverse() # Sort back to chronological order for the chart

        # Prepare data for charts (e.g., P&L history)
        pnl_dates = []
        pnl_values = []
        for data in pnl_history_data:
            pnl_dates.append(data['date'].strftime('%Y-%m-%d'))
            pnl_values.append(data['pnl'])

        return render_template('dashboard.html',
                               account_balance=account_balance,
                               positions=positions,
                               gain_loss=gain_loss,
                               total_equity=total_equity,
                               pnl_today=pnl_today,
                               pnl_total=pnl_total,
                               recent_trades=recent_trades,
                               pnl_dates=pnl_dates,
                               pnl_values=pnl_values)

    except Exception as e:
        handle_route_exception(e, 'dashboard')
        return render_template('dashboard.html',
                               account_balance={},
                               positions=[],
                               gain_loss={},
                               total_equity=0,
                               pnl_today=0,
                               pnl_total=0,
                               recent_trades=[],
                               pnl_dates=[],
                               pnl_values=[])


def _handle_equity_trade(symbol, side, quantity, order_type, duration, price):
    return tradier_equity_order.order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        duration=duration,
        price=float(price) if price else None
    )

def _handle_option_trade(option_symbol, side, quantity, order_type, duration, price):
    return tradier_options_order.options_order(
        occ_symbol=option_symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        duration=duration,
        price=float(price) if price else None
    )

@app.route('/trade', methods=['GET', 'POST'])
@login_required
def trade():
    if request.method == 'POST':
        trade_type = request.form.get('trade_type')
        symbol = request.form.get('symbol').upper() if request.form.get('symbol') else ''
        side = request.form.get('side')
        try:
            quantity = int(request.form.get('quantity'))
            if quantity <= 0:
                raise ValueError("Quantity must be positive.")
        except (TypeError, ValueError):
            flash('Invalid quantity. Quantity must be a positive integer.', 'danger')
            return render_template('trade.html')

        order_type = request.form.get('order_type')
        duration = request.form.get('duration')
        price = request.form.get('price') # For limit orders
        option_symbol = request.form.get('option_symbol') # For options

        try:
            if not current_user.tradier_account_id or not current_user.tradier_access_token:
                flash('You must configure your Tradier account credentials to trade.', 'danger')
                return render_template('trade.html')

            user_equity_order = EquityOrder(current_user.tradier_account_id, current_user.tradier_access_token, live_trade=tradier_live_trading)
            user_options_order = OptionsOrder(current_user.tradier_account_id, current_user.tradier_access_token, live_trade=tradier_live_trading)

            order_response = None
            if trade_type == 'equity':
                order_response = _handle_equity_trade(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    order_type=order_type,
                    duration=duration,
                    price=price
                )
            elif trade_type == 'option':
                if not option_symbol:
                    flash('Option symbol is required for options trades.', 'danger')
                    return render_template('trade.html')

                order_response = _handle_option_trade(
                    option_symbol=option_symbol,
                    side=side,
                    quantity=quantity,
                    order_type=order_type,
                    duration=duration,
                    price=price
                )

            if order_response and order_response.get('orders') and order_response['orders'].get('order') and order_response['orders']['order'].get('status') == 'ok':
                flash(f'Order placed successfully! Order ID: {order_response["orders"]["order"]["id"]}', 'success')
                # Store trade in MongoDB for P&L tracking
                trades_collection.insert_one({
                    'user_id': current_user.id,
                    'symbol': symbol,
                    'trade_type': trade_type,
                    'side': side,
                    'quantity': quantity,
                    'order_type': order_type,
                    'duration': duration,
                    'price_placed': float(price) if price else None,
                    'option_symbol': option_symbol,
                    'order_id': order_response["orders"]["order"]["id"],
                    'timestamp': datetime.now()
                })
            else:
                error_message = "Failed to place order."
                if order_response and order_response.get('errors'):
                    error_message += f" Errors: {order_response['errors']['error']}"
                flash(error_message, 'danger')

        except Exception as e:
            handle_route_exception(e, 'trade')

    return render_template('trade.html')

def _handle_api_error(e, action, symbol):
    app.logger.exception(f"An unexpected error occurred while getting {action} for {symbol}")
    return {'error': str(e)}, 500

@app.route('/get_quote/<symbol>')
@login_required
def get_quote(symbol):
    try:
        quote_data = tradier_quotes.get_quote_data([symbol])
        if quote_data and quote_data.get('quotes') and quote_data['quotes'].get('quote'):
            quote = quote_data['quotes']['quote']
            return {
                'symbol': quote.get('symbol'),
                'description': quote.get('description'),
                'last': quote.get('last'),
                'change': quote.get('change'),
                'change_percentage': quote.get('change_percentage'),
                'bid': quote.get('bid'),
                'ask': quote.get('ask'),
                'volume': quote.get('volume')
            }
        return {'error': 'Quote not found'}, 404
    except Exception as e:
        return _handle_api_error(e, "quote", symbol)

@app.route('/get_option_chain/<symbol>')
@login_required
@cachetools.func.ttl_cache(maxsize=128, ttl=60)
def get_option_chain(symbol):
    try:
        option_chain = tradier_options_data.get_chain_day(symbol)
        if option_chain and option_chain.get('options') and option_chain['options'].get('option'):
            return {'options': option_chain['options']['option']}
        return {'error': 'Option chain not found'}, 404
    except Exception as e:
        return _handle_api_error(e, "option chain", symbol)

# Helper to update P&L snapshot (can be a scheduled task in a real app)
def update_pnl_snapshot():
    def process_user_pnl(user_doc, now):
        user_tradier_account_id = user_doc.get('tradier_account_id')
        user_tradier_access_token = user_doc.get('tradier_access_token')

        if user_tradier_account_id and user_tradier_access_token:
            try:
                tradier_account_instance = Account(user_tradier_account_id, user_tradier_access_token, live_trade=tradier_live_trading)
                account_balance = tradier_account_instance.get_account_balance()
                current_pnl = account_balance.get('realized_gain_loss', 0) + account_balance.get('unrealized_gain_loss', 0)
                total_equity = account_balance.get('total_equity', 0)

                return {
                    'user_id': str(user_doc['_id']),
                    'date': now,
                    'pnl': current_pnl,
                    'total_equity': total_equity
                }
            except Exception as e:
                app.logger.exception(f"Error preparing P&L for user {user_doc['_id']}")
        return None

    with app.app_context(): # Ensure app context for database operations
        pnl_snapshots = []
        now = datetime.now()

        query = {
            'tradier_account_id': {'$exists': True, '$ne': None},
            'tradier_access_token': {'$exists': True, '$ne': None}
        }
        projection = {'_id': 1, 'tradier_account_id': 1, 'tradier_access_token': 1}

        user_docs = list(users_collection.find(query, projection))

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_user_pnl, doc, now) for doc in user_docs]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    pnl_snapshots.append(result)

        if pnl_snapshots:
            try:
                pnl_collection.insert_many(pnl_snapshots)
                print(f"P&L snapshots updated for {len(pnl_snapshots)} users.")
            except Exception as e:
                app.logger.exception("Error inserting P&L snapshots")

# Example of how you might trigger a P&L snapshot (in a real app, use a scheduler like APScheduler)
@app.route('/update_pnl_manual')
@login_required
def manual_pnl_update():
    try:
        update_pnl_snapshot()
        flash('P&L snapshot updated.', 'success')
    except Exception as e:
        flash(f'Error updating P&L snapshot: {e}', 'danger')
    return redirect(url_for('dashboard'))

# --- Run the app ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=app.config.get('DEBUG', False))