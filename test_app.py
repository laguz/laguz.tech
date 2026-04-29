import unittest
import os
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

class TestApp(unittest.TestCase):
    def setUp(self):
        app.app.config['TESTING'] = True
        app.app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.app.test_client()

        # Mock database for user auth
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

    def tearDown(self):
        self.patcher.stop()

    @patch('app.tradier_quotes.get_quote_data')
    def test_get_quote_missing_quote(self, mock_get_quote_data):
        # Log in the user
        self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password
        })

        # Mock the return value to be empty or missing 'quotes'
        mock_get_quote_data.return_value = {}

        # Perform the GET request
        response = self.client.get('/get_quote/UNKNOWN')

        # Assert correct error and status code
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {'error': 'Quote not found'})

    def test_register_password_mismatch(self):
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password456'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords do not match!', response.data)

if __name__ == '__main__':
    unittest.main()
