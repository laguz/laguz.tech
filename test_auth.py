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

from bson.objectid import ObjectId

# Import app after environment variables are set
from app import app, users_collection, load_user

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

    def test_load_user_success(self):
        # Insert a user to get a valid ObjectId
        user_data = {
            'username': 'loaduser_test',
            'email': 'loaduser@example.com',
            'password': generate_password_hash('password123')
        }
        result = self.mock_users.insert_one(user_data)
        user_id = result.inserted_id

        # Call load_user and verify it returns a User object with correct attributes
        with patch('app.users_collection.find_one') as mock_find_one:
            mock_find_one.return_value = {
                '_id': user_id,
                'username': 'loaduser_test',
                'password': 'hashed_password'
            }
            user = load_user(str(user_id))

            self.assertIsNotNone(user)
            self.assertEqual(user.id, str(user_id))
            self.assertEqual(user.username, 'loaduser_test')
            self.assertEqual(user.password_hash, 'hashed_password')
            mock_find_one.assert_called_once_with({'_id': ObjectId(str(user_id))})

    def test_load_user_not_found(self):
        # Generate a non-existent ObjectId string
        non_existent_id = str(ObjectId())

        # Call load_user with the non-existent ID
        with patch('app.users_collection.find_one') as mock_find_one:
            mock_find_one.return_value = None
            user = load_user(non_existent_id)

            # Verify it returns None
            self.assertIsNone(user)
            mock_find_one.assert_called_once_with({'_id': ObjectId(non_existent_id)})

if __name__ == '__main__':
    unittest.main()
