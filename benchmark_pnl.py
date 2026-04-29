import time
import os
import concurrent.futures
from unittest.mock import patch, MagicMock

# Set environment variables for config
os.environ['SECRET_KEY'] = 'test_secret'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/'
os.environ['TRADIER_ACCESS_TOKEN'] = 'test_token'
os.environ['TRADIER_ACCOUNT_ID'] = 'test_account'
os.environ['TRADIER_LIVE_TRADING'] = '0'

import app

# Mock the database
app.users_collection.find = MagicMock(return_value=[
    {'_id': f'user_{i}'} for i in range(100)
])

# Mock the Tradier API to simulate a 100ms response time
def mock_get_account_balance():
    time.sleep(0.1) # Simulate network delay
    return {
        'realized_gain_loss': 100,
        'unrealized_gain_loss': 50,
        'total_equity': 10000
    }

# Measure the CURRENT implementation (ThreadPoolExecutor)
@patch('app.Account.get_account_balance', side_effect=mock_get_account_balance)
@patch('app.pnl_collection.insert_many')
def run_current_benchmark(mock_insert, mock_api):
    start = time.time()
    app.update_pnl_snapshot()
    end = time.time()
    print(f"Current Implementation (ThreadPoolExecutor): {end - start:.4f} seconds")
    print(f"API Calls made: {mock_api.call_count}")

# Measure the PROPOSED implementation (O(1) API call)
def proposed_update_pnl_snapshot():
    with app.app.app_context():
        pnl_snapshots = []
        user_ids = [str(user_doc['_id']) for user_doc in app.users_collection.find({})]

        # O(1) API call
        try:
            tradier_account_instance = app.Account(app.tradier_account_id, app.tradier_access_token, live_trade=app.tradier_live_trading)
            account_balance = tradier_account_instance.get_account_balance()
            current_pnl = account_balance.get('realized_gain_loss', 0) + account_balance.get('unrealized_gain_loss', 0)
            total_equity = account_balance.get('total_equity', 0)
            now = app.datetime.now()

            for user_id in user_ids:
                pnl_snapshots.append({
                    'user_id': user_id,
                    'date': now,
                    'pnl': current_pnl,
                    'total_equity': total_equity
                })
        except Exception as e:
            print(f"Error fetching global account balance: {e}")
            return

        if pnl_snapshots:
            try:
                app.pnl_collection.insert_many(pnl_snapshots)
                # print(f"P&L snapshots updated for {len(pnl_snapshots)} users.")
            except Exception as e:
                pass

@patch('app.Account.get_account_balance', side_effect=mock_get_account_balance)
@patch('app.pnl_collection.insert_many')
def run_proposed_benchmark(mock_insert, mock_api):
    start = time.time()
    proposed_update_pnl_snapshot()
    end = time.time()
    print(f"Proposed Implementation (O(1) API call): {end - start:.4f} seconds")
    print(f"API Calls made: {mock_api.call_count}")

if __name__ == '__main__':
    print("Running benchmarks for 100 users with 100ms simulated API delay...")
    run_current_benchmark()
    run_proposed_benchmark()
