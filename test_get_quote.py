import unittest
import json
from unittest.mock import patch
from test_base import BaseTestCase

class TestGetQuote(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Patch tradier_quotes.get_quote_data
        self.patcher_quotes = patch('app.tradier_quotes.get_quote_data')
        self.mock_get_quote_data = self.patcher_quotes.start()

    def tearDown(self):
        super().tearDown()
        self.patcher_quotes.stop()

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

if __name__ == '__main__':
    unittest.main()
