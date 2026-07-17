import unittest
import json
from unittest.mock import patch
from test_base import BaseTestCase

class TestGetOptionChain(BaseTestCase):

    def setUp(self):
        super().setUp()
        # Patch tradier_options_data.get_chain_day
        self.patcher_chain = patch('app.tradier_options_data.get_chain_day')
        self.mock_get_chain_day = self.patcher_chain.start()

    def tearDown(self):
        super().tearDown()
        self.patcher_chain.stop()

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
