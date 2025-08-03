from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime, timedelta
import requests
from uvatradier import Tradier, Account, Quotes, OptionsData, EquityOrder, OptionsOrder
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

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

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# --- Routes ---

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
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
            return redirect(next_page or url_for('dashboard'))
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

        if users_collection.find_one({'username': username}):
            flash('Username already exists. Please choose a different one.', 'warning')
            return render_template('register.html', username=username)
        
        if users_collection.find_one({'username': email}):
            flash('Username already exists. Please choose a different one.', 'warning')
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
        # Get account balances and positions from Tradier
        account_balance = tradier_account.get_account_balance()
        positions = tradier_account.get_positions()
        gain_loss = tradier_account.get_gainloss()

        # Calculate P&L (simplified - you'll want to store this more robustly)
        total_equity = account_balance.get('total_equity', 0)
        total_market_value = account_balance.get('total_market_value', 0)
        pnl_today = account_balance.get('realized_day_gain_loss', 0) + account_balance.get('unrealized_day_gain_loss', 0) # Example of combining
        pnl_total = account_balance.get('realized_gain_loss', 0) + account_balance.get('unrealized_gain_loss', 0) # Example of combining

        # Fetch recent trades from your MongoDB (up to N trades)
        recent_trades = trades_collection.find({'user_id': current_user.id}).sort('timestamp', -1).limit(10)

        # Fetch P&L history from your MongoDB
        pnl_history_data = list(pnl_collection.find({'user_id': current_user.id}).sort('date', 1))

        # Prepare data for charts (e.g., P&L history)
        pnl_dates = [data['date'].strftime('%Y-%m-%d') for data in pnl_history_data]
        pnl_values = [data['pnl'] for data in pnl_history_data]

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

    except requests.exceptions.RequestException as e:
        flash(f"Error connecting to Tradier API: {e}", 'danger')
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
    except Exception as e:
        flash(f"An unexpected error occurred: {e}", 'danger')
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


@app.route('/trade', methods=['GET', 'POST'])
@login_required
def trade():
    if request.method == 'POST':
        trade_type = request.form.get('trade_type')
        symbol = request.form.get('symbol').upper()
        side = request.form.get('side')
        quantity = int(request.form.get('quantity'))
        order_type = request.form.get('order_type')
        duration = request.form.get('duration')
        price = request.form.get('price') # For limit orders
        option_symbol = request.form.get('option_symbol') # For options

        try:
            order_response = None
            if trade_type == 'equity':
                order_response = tradier_equity_order.order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    order_type=order_type,
                    duration=duration,
                    price=float(price) if price else None
                )
            elif trade_type == 'option':
                if not option_symbol:
                    flash('Option symbol is required for options trades.', 'danger')
                    return render_template('trade.html')

                # Get option chain to validate or help user select
                # This is a good place to add logic to help find the OCC symbol
                # Example: option_chain = tradier_options_data.get_chain_day(symbol)
                # You'd typically need to parse this to get the specific OCC symbol for a strike/expiry

                order_response = tradier_options_order.options_order(
                    occ_symbol=option_symbol,
                    side=side,
                    quantity=quantity,
                    order_type=order_type,
                    duration=duration,
                    price=float(price) if price else None
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

        except requests.exceptions.RequestException as e:
            flash(f"Error communicating with Tradier API: {e}", 'danger')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')

    return render_template('trade.html')

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
        return {'error': str(e)}, 500

@app.route('/get_option_chain/<symbol>')
@login_required
def get_option_chain(symbol):
    try:
        option_chain = tradier_options_data.get_chain_day(symbol)
        if option_chain and option_chain.get('options') and option_chain['options'].get('option'):
            return {'options': option_chain['options']['option']}
        return {'error': 'Option chain not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500

# Helper to update P&L snapshot (can be a scheduled task in a real app)
def update_pnl_snapshot():
    with app.app_context(): # Ensure app context for database operations
        for user_doc in users_collection.find({}):
            user_id = str(user_doc['_id'])
            try:
                tradier_account_instance = Account(tradier_account_id, tradier_access_token, live_trade=tradier_live_trading)
                account_balance = tradier_account_instance.get_account_balance()
                current_pnl = account_balance.get('realized_gain_loss', 0) + account_balance.get('unrealized_gain_loss', 0)

                pnl_collection.insert_one({
                    'user_id': user_id,
                    'date': datetime.now(),
                    'pnl': current_pnl,
                    'total_equity': account_balance.get('total_equity', 0)
                })
                print(f"P&L snapshot updated for user {user_id}: {current_pnl}")
            except Exception as e:
                print(f"Error updating P&L for user {user_id}: {e}")

# Example of how you might trigger a P&L snapshot (in a real app, use a scheduler like APScheduler)
@app.route('/update_pnl_manual')
@login_required
def manual_pnl_update():
    update_pnl_snapshot()
    flash('P&L snapshot updated.', 'success')
    return redirect(url_for('dashboard'))

# --- Run the app ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)