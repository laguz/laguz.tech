import unittest
import os
import requests
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
from werkzeug.security import generate_password_hash
from unittest.mock import patch
import mongomock

class MockRequestException(requests.exceptions.RequestException):
    pass

class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.app.test_client()

    def setUp(self):
        self.mock_db = mongomock.MongoClient().db
        self.patcher = patch('app.users_collection', self.mock_db.users)
        self.mock_users = self.patcher.start()

        # Add a test user
        self.test_username = 'testuser'
        self.test_password = 'password123'
        self.mock_users.insert_one({
            'username': self.test_username,
            'email': 'testuser@example.com',
            'password': generate_password_hash(self.test_password)
        })

        self.client = app.app.test_client()

        # Create a mongomock database and patch the users collection
        self.mock_db = mongomock.MongoClient().db
        self.patcher = patch('app.users_collection', self.mock_db.users)
        self.mock_users = self.patcher.start()

        # Set up a test user in the integration DB
        self.test_username = 'integration_user'
        self.test_password = 'integration_password'

        # Insert test user
        self.mock_users.insert_one({
            'username': self.test_username,
            'email': 'integration@example.com',
            'password': generate_password_hash(self.test_password)
        })

    def tearDown(self):
        # Clean up
        self.patcher.stop()

    def test_login_success(self):
        response = self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logged in successfully!', response.data)

    def test_login_invalid(self):
        response = self.client.post('/login', data={
            'username': self.test_username,
            'password': 'wrong_password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password.', response.data)

    def test_register_password_mismatch(self):
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password456'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords do not match!', response.data)

    @patch('app.tradier_account.get_account_balance')
    def test_dashboard_exception_handling(self, mock_get_account_balance):
        mock_get_account_balance.side_effect = MockRequestException("Test exception")

        # login
        self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password
        })

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Error connecting to Tradier API: Test exception', response.data)
        self.assertIn(b'No open positions.', response.data)
        self.assertIn(b'No recent trades.', response.data)
        self.assertIn(b'$0.00', response.data)

if __name__ == '__main__':
    unittest.main()
