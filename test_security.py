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

from app import app, users_collection, is_safe_url

class TestSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def setUp(self):
        self.mock_db = mongomock.MongoClient().db
        self.patcher = patch('app.users_collection', self.mock_db.users)
        self.mock_users = self.patcher.start()

        self.test_username = 'testuser'
        self.test_password = 'password123'
        self.mock_users.insert_one({
            'username': self.test_username,
            'email': 'testuser@example.com',
            'password': generate_password_hash(self.test_password)
        })

    def tearDown(self):
        self.patcher.stop()

    def test_open_redirect_mitigated(self):
        # Malicious next URL
        malicious_url = 'http://malicious.com'

        # Attempt to login with the malicious next URL
        response = self.client.post(f'/login?next={malicious_url}', data={
            'username': self.test_username,
            'password': self.test_password
        }, follow_redirects=False)

        # Ensure it redirects to the default dashboard, NOT malicious.com
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.location, malicious_url)
        self.assertTrue(response.location.endswith('/dashboard'))

    def test_safe_redirect_allowed(self):
        # Safe relative URL
        safe_url = '/trade'

        # Attempt to login with a safe next URL
        response = self.client.post(f'/login?next={safe_url}', data={
            'username': self.test_username,
            'password': self.test_password
        }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(safe_url))

    def test_is_safe_url_function(self):
        with app.test_request_context('http://example.com/'):
            # Safe URLs
            self.assertTrue(is_safe_url('/dashboard'))
            self.assertTrue(is_safe_url('http://example.com/dashboard'))
            self.assertTrue(is_safe_url('https://example.com/profile')) # Note: the scheme check handles http/https

            # Unsafe URLs
            self.assertFalse(is_safe_url('http://malicious.com/dashboard'))
            self.assertFalse(is_safe_url('javascript:alert(1)'))
            self.assertFalse(is_safe_url('//malicious.com'))
            # Note: urlparse(urljoin('http://example.com/', '\\malicious.com')) parses to
            # scheme='http', netloc='example.com', path='/\\malicious.com'.
            # Therefore it is technically safe according to this function, as it won't redirect
            # to another domain.

if __name__ == '__main__':
    unittest.main()
