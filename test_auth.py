import os
import unittest
from unittest.mock import patch
import mongomock
from werkzeug.security import generate_password_hash

# Set environment variables before importing app to avoid config validation errors
os.environ['SECRET_KEY'] = 'test_secret'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/test_db'
os.environ['TRADIER_ACCESS_TOKEN'] = 'test_token'
os.environ['TRADIER_ACCOUNT_ID'] = 'test_account'
os.environ['TRADIER_LIVE_TRADING'] = 'False'

# Import app after environment variables are set
from app import app, users_collection

class TestAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def setUp(self):
        # Create a mongomock database and patch the users collection
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

    def test_login_success(self):
        # Test valid login credentials
        response = self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password
        }, follow_redirects=False)

        # Verify successful login redirects
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/dashboard'))

    def test_login_invalid_password(self):
        # Test invalid password
        response = self.client.post('/login', data={
            'username': self.test_username,
            'password': 'wrongpassword'
        }, follow_redirects=False)

        # Verify failed login returns 200 OK without redirecting
        self.assertEqual(response.status_code, 200)

    def test_login_invalid_username(self):
        # Test invalid username
        response = self.client.post('/login', data={
            'username': 'wronguser',
            'password': self.test_password
        }, follow_redirects=False)

        # Verify failed login returns 200 OK without redirecting
        self.assertEqual(response.status_code, 200)

    def test_login_redirect_authenticated_user(self):
        # First, log in the user
        self.client.post('/login', data={
            'username': self.test_username,
            'password': self.test_password
        })

        # Then, try to access the login page again via GET
        response = self.client.get('/login', follow_redirects=False)

        # Verify user is redirected to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/dashboard'))

if __name__ == '__main__':
    unittest.main()
