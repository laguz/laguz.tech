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
    {
        '_id': f'user_{i}',
        'tradier_account_id': f'account_{i}',
        'tradier_access_token': f'token_{i}'
    } for i in range(100)
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
        now = app.datetime.now()

        for user_doc in app.users_collection.find({}):
            user_tradier_account_id = user_doc.get('tradier_account_id')
            user_tradier_access_token = user_doc.get('tradier_access_token')

            if user_tradier_account_id and user_tradier_access_token:
                try:
                    tradier_account_instance = app.Account(user_tradier_account_id, user_tradier_access_token, live_trade=app.tradier_live_trading)
                    account_balance = tradier_account_instance.get_account_balance()
                    current_pnl = account_balance.get('realized_gain_loss', 0) + account_balance.get('unrealized_gain_loss', 0)
                    total_equity = account_balance.get('total_equity', 0)

                    pnl_snapshots.append({
                        'user_id': str(user_doc['_id']),
                        'date': now,
                        'pnl': current_pnl,
                        'total_equity': total_equity
                    })
                except Exception as e:
                    print(f"Error preparing P&L for user {user_doc['_id']}: {e}")

        if pnl_snapshots:
            try:
                app.pnl_collection.insert_many(pnl_snapshots)
            except Exception as e:
                print(f"Error inserting P&L snapshots: {e}")

@patch('app.Account.get_account_balance', side_effect=mock_get_account_balance)
@patch('app.pnl_collection.insert_many')
def run_proposed_benchmark(mock_insert, mock_api):
    start = time.time()
    proposed_update_pnl_snapshot()
    end = time.time()
    print(f"Proposed Implementation (O(1) API call): {end - start:.4f} seconds")
    print(f"API Calls made: {mock_api.call_count}")

if __name__ == '__main__':
    gen = DataGenerator(100)
    for_time = timeit.timeit(gen.benchmark_for_loop, number=10000)
    list_comp_time = timeit.timeit(gen.benchmark_list_comp, number=10000)
    zip_time = timeit.timeit(gen.benchmark_zip_list_comp, number=10000)
    print(f"For loop (N=100): {for_time:.5f}s")
    print(f"List comp (N=100): {list_comp_time:.5f}s")
    print(f"Zip List comp (N=100): {zip_time:.5f}s")

    gen = DataGenerator(1000)
    for_time = timeit.timeit(gen.benchmark_for_loop, number=1000)
    list_comp_time = timeit.timeit(gen.benchmark_list_comp, number=1000)
    zip_time = timeit.timeit(gen.benchmark_zip_list_comp, number=1000)
    print(f"For loop (N=1000): {for_time:.5f}s")
    print(f"List comp (N=1000): {list_comp_time:.5f}s")
    print(f"Zip List comp (N=1000): {zip_time:.5f}s")

    gen = DataGenerator(10000)
    for_time = timeit.timeit(gen.benchmark_for_loop, number=100)
    list_comp_time = timeit.timeit(gen.benchmark_list_comp, number=100)
    zip_time = timeit.timeit(gen.benchmark_zip_list_comp, number=100)
    print(f"For loop (N=10000): {for_time:.5f}s")
    print(f"List comp (N=10000): {list_comp_time:.5f}s")
    print(f"Zip List comp (N=10000): {zip_time:.5f}s")
