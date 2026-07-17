import unittest
import os
import json
from unittest.mock import patch
import mongomock
from werkzeug.security import generate_password_hash

# Set required environment variables before importing app
os.environ['SECRET_KEY'] = 'test_secret'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/test_db'
os.environ['TRADIER_ACCESS_TOKEN'] = 'test_token'
os.environ['TRADIER_ACCOUNT_ID'] = 'test_account'
os.environ['TRADIER_LIVE_TRADING'] = 'false'

import requests

class MockRequestException(requests.exceptions.RequestException):
    pass

import app

class TestGetQuote(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.app.test_client()

    def setUp(self):
        # Mock database
        self.mock_db = mongomock.MongoClient().db
        self.patcher_users = patch('app.users_collection', self.mock_db.users)
        self.mock_users = self.patcher_users.start()

        # Add a test user
        self.test_username = 'testuser'
        self.test_password = 'password123'
        self.user_id = self.mock_users.insert_one({
            'username': self.test_username,
            'email': 'testuser@example.com',
            'password': generate_password_hash(self.test_password)
        }).inserted_id

        # Patch tradier_quotes.get_quote_data
        self.patcher_quotes = patch('app.tradier_quotes.get_quote_data')
        self.mock_get_quote_data = self.patcher_quotes.start()

    def tearDown(self):
        self.patcher_users.stop()
        self.patcher_quotes.stop()

    def login(self):
        return self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password
        }, follow_redirects=True)

    def test_get_quote_success(self):
        self.login()
        # Mock successful quote data
        self.mock_get_quote_data.return_value = {
            'quotes': {
                'quote': {
                    'symbol': 'AAPL',
                    'description': 'Apple Inc',
                    'last': 150.00,
                    'change': 1.23,
                    'change_percentage': 0.82,
                    'bid': 149.90,
                    'ask': 150.10,
                    'volume': 1000000
                }
            }
        }

        response = self.client.get('/get_quote/AAPL')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['symbol'], 'AAPL')
        self.assertEqual(data['last'], 150.00)
        self.assertEqual(data['description'], 'Apple Inc')

    def test_get_quote_not_found(self):
        self.login()
        # Mock missing quote data
        self.mock_get_quote_data.return_value = {
            'quotes': {
                'quote': None
            }
        }

        response = self.client.get('/get_quote/INVALID')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Quote not found')

    def test_get_quote_unauthorized(self):
        # No login
        response = self.client.get('/get_quote/AAPL')
        # Should redirect to login because of @login_required
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_get_quote_internal_error(self):
        self.login()
        # Mock exception
        self.mock_get_quote_data.side_effect = Exception("API error")

        response = self.client.get('/get_quote/AAPL')
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'API error')

    @patch('app.app.logger.exception')
    def test_get_quote_request_exception(self, mock_logger):
        self.login()

        # Reset the mock because login() might trigger an unexpected dashboard error
        # in some test environments without a real mongo connection
        mock_logger.reset_mock()

        # Mock RequestException
        self.mock_get_quote_data.side_effect = MockRequestException("Request failed")

        response = self.client.get('/get_quote/AAPL')
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Request failed')
        mock_logger.assert_called_once_with("An unexpected error occurred while getting quote for AAPL")

if __name__ == '__main__':
    unittest.main()
