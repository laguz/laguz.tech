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

import app

class TestGetOptionChain(unittest.TestCase):
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

        # Patch tradier_options_data.get_chain_day
        self.patcher_chain = patch('app.tradier_options_data.get_chain_day')
        self.mock_get_chain_day = self.patcher_chain.start()

    def tearDown(self):
        self.patcher_users.stop()
        self.patcher_chain.stop()

    def login(self):
        return self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password
        }, follow_redirects=True)

    def test_get_option_chain_success(self):
        self.login()
        # Mock successful option chain data
        self.mock_get_chain_day.return_value = {
            'options': {
                'option': [
                    {
                        'symbol': 'AAPL211119C00150000',
                        'description': 'AAPL Nov 19 2021 150.00 Call',
                        'strike': 150.0,
                        'option_type': 'call',
                        'expiration_date': '2021-11-19',
                        'bid': 5.0,
                        'ask': 5.2,
                        'volume': 1000
                    }
                ]
            }
        }

        response = self.client.get('/get_option_chain/AAPL')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('options', data)
        self.assertEqual(len(data['options']), 1)
        self.assertEqual(data['options'][0]['symbol'], 'AAPL211119C00150000')

    def test_get_option_chain_not_found(self):
        self.login()
        # Mock missing or invalid structure
        self.mock_get_chain_day.return_value = {
            'options': None
        }

        response = self.client.get('/get_option_chain/INVALID')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Option chain not found')

    def test_get_option_chain_unauthorized(self):
        # No login
        response = self.client.get('/get_option_chain/AAPL')
        # Should redirect to login because of @login_required
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_get_option_chain_internal_error(self):
        self.login()
        # Mock exception
        self.mock_get_chain_day.side_effect = Exception("API error")

        response = self.client.get('/get_option_chain/AAPL')
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'API error')

if __name__ == '__main__':
    unittest.main()
