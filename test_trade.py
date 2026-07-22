import unittest
import os
from unittest.mock import patch
import mongomock
from werkzeug.security import generate_password_hash

os.environ['SECRET_KEY'] = 'test_secret'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/test_db'
os.environ['TRADIER_ACCESS_TOKEN'] = 'test_token'
os.environ['TRADIER_ACCOUNT_ID'] = 'test_account'
os.environ['TRADIER_LIVE_TRADING'] = 'false'

import app

class TestTrade(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.app.test_client()

    def setUp(self):
        self.mock_db = mongomock.MongoClient().db
        self.patcher_users = patch('app.users_collection', self.mock_db.users)
        self.mock_users = self.patcher_users.start()

        self.patcher_trades = patch('app.trades_collection', self.mock_db.trades)
        self.mock_trades = self.patcher_trades.start()

        self.test_username = 'testuser'
        self.test_password = 'StrongPass123!'
        self.user_id = self.mock_users.insert_one({
            'username': self.test_username,
            'email': 'testuser@example.com',
            'password': generate_password_hash(self.test_password),
            'tradier_account_id': 'test_user_account',
            'tradier_access_token': 'test_user_token'
        }).inserted_id

        self.patcher_equity_order = patch('app.EquityOrder.order')
        self.mock_equity_order = self.patcher_equity_order.start()

        self.patcher_options_order = patch('app.OptionsOrder.options_order')
        self.mock_options_order = self.patcher_options_order.start()

    def tearDown(self):
        self.patcher_users.stop()
        self.patcher_trades.stop()
        self.patcher_equity_order.stop()
        self.patcher_options_order.stop()

    def login(self):
        self.client.post('/login', data={'username': self.test_username, 'password': self.test_password})

    def test_trade_equity_success(self):
        self.login()
        self.mock_equity_order.return_value = {'orders': {'order': {'status': 'ok', 'id': '12345'}}}
        response = self.client.post('/trade', data={
            'trade_type': 'equity',
            'symbol': 'aapl',
            'side': 'buy',
            'quantity': '10',
            'order_type': 'market',
            'duration': 'day',
            'price': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Order placed successfully! Order ID: 12345', response.data)

        # Verify db insert
        trade = self.mock_trades.find_one({'order_id': '12345'})
        self.assertIsNotNone(trade)
        self.assertEqual(trade['symbol'], 'AAPL')
        self.assertEqual(trade['trade_type'], 'equity')

    def test_trade_option_missing_symbol(self):
        self.login()
        response = self.client.post('/trade', data={
            'trade_type': 'option',
            'symbol': 'aapl',
            'side': 'buy_to_open',
            'quantity': '1',
            'order_type': 'market',
            'duration': 'day',
            'price': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Option symbol is required for options trades.', response.data)
        self.mock_options_order.assert_not_called()

    def test_trade_option_success(self):
        self.login()
        self.mock_options_order.return_value = {'orders': {'order': {'status': 'ok', 'id': '67890'}}}
        response = self.client.post('/trade', data={
            'trade_type': 'option',
            'symbol': 'aapl',
            'option_symbol': 'AAPL240119C00150000',
            'side': 'buy_to_open',
            'quantity': '2',
            'order_type': 'market',
            'duration': 'day',
            'price': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Order placed successfully! Order ID: 67890', response.data)

        # Verify db insert
        trade = self.mock_trades.find_one({'order_id': '67890'})
        self.assertIsNotNone(trade)
        self.assertEqual(trade['symbol'], 'AAPL')
        self.assertEqual(trade['trade_type'], 'option')
        self.assertEqual(trade['option_symbol'], 'AAPL240119C00150000')

    def test_trade_api_failure(self):
        self.login()
        self.mock_equity_order.return_value = {'errors': {'error': 'Invalid symbol'}}
        response = self.client.post('/trade', data={
            'trade_type': 'equity',
            'symbol': 'INVALID',
            'side': 'buy',
            'quantity': '1',
            'order_type': 'market',
            'duration': 'day',
            'price': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Failed to place order. Errors: Invalid symbol', response.data)
        self.assertEqual(self.mock_trades.count_documents({}), 0)

    def test_trade_invalid_quantity(self):
        self.login()
        response = self.client.post('/trade', data={
            'trade_type': 'equity',
            'symbol': 'aapl',
            'side': 'buy',
            'quantity': '-10',
            'order_type': 'market',
            'duration': 'day',
            'price': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid quantity. Quantity must be a positive integer.', response.data)
        self.mock_equity_order.assert_not_called()

    def test_trade_missing_credentials(self):
        # Create a user without Tradier credentials
        no_cred_username = 'nocreduser'
        no_cred_password = 'StrongPass123!'
        self.mock_users.insert_one({
            'username': no_cred_username,
            'email': 'nocreduser@example.com',
            'password': generate_password_hash(no_cred_password)
        })
        self.client.post('/login', data={'username': no_cred_username, 'password': no_cred_password})

        response = self.client.post('/trade', data={
            'trade_type': 'equity',
            'symbol': 'aapl',
            'side': 'buy',
            'quantity': '10',
            'order_type': 'market',
            'duration': 'day',
            'price': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You must configure your Tradier account credentials to trade.', response.data)
        self.mock_equity_order.assert_not_called()

if __name__ == '__main__':
    unittest.main()
