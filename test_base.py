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

class BaseTestCase(unittest.TestCase):
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

    def tearDown(self):
        self.patcher_users.stop()

    def login(self):
        return self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password
        }, follow_redirects=True)
