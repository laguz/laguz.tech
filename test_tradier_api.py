import sys
from unittest.mock import MagicMock, patch

# Mock dependencies before import because they are not installed in this environment.
# In a real CI environment, these should be installed via pip.
# We have installed requests now, so no need for this pre-mocking
# if 'requests' not in sys.modules:
#     sys.modules['requests'] = MagicMock()
if 'dotenv' not in sys.modules:
    sys.modules['dotenv'] = MagicMock()

import unittest
import requests
from tradier_api import TradierAPI

class TestTradierAPIQuotes(unittest.TestCase):
    def setUp(self):
        # Initialize TradierAPI with dummy values
        self.api = TradierAPI(access_token='fake_token', base_url='https://api.tradier.com/v1')

    def test_get_quotes_single_symbol(self):
        """Test get_quotes with a single symbol string."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            self.api.get_quotes('AAPL')

            mock_make_request.assert_called_once_with(
                'markets/quotes',
                {'symbols': 'AAPL', 'greeks': 'false'}
            )

    def test_get_quotes_multiple_symbols(self):
        """Test get_quotes with a list of symbols."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            symbols = ['AAPL', 'MSFT', 'GOOGL']
            self.api.get_quotes(symbols)

            mock_make_request.assert_called_once_with(
                'markets/quotes',
                {'symbols': 'AAPL,MSFT,GOOGL', 'greeks': 'false'}
            )

    def test_get_quotes_none_input(self):
        """Test get_quotes handles None input gracefully."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            result = self.api.get_quotes(None)
            self.assertIsNone(result)
            mock_make_request.assert_not_called()

    def test_get_quotes_empty_list(self):
        """Test get_quotes handles empty list input gracefully."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            result = self.api.get_quotes([])
            self.assertIsNone(result)
            mock_make_request.assert_not_called()

    def test_get_history_basic(self):
        """Test get_history with basic parameters."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            self.api.get_history('AAPL')
            mock_make_request.assert_called_once_with(
                'markets/history',
                {'symbol': 'AAPL', 'interval': 'daily'}
            )

    def test_get_history_with_dates(self):
        """Test get_history with start and end dates."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            self.api.get_history('AAPL', start='2023-01-01', end='2023-12-31')
            mock_make_request.assert_called_once_with(
                'markets/history',
                {'symbol': 'AAPL', 'interval': 'daily', 'start': '2023-01-01', 'end': '2023-12-31'}
            )

    def test_get_option_chains(self):
        """Test get_option_chains."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            self.api.get_option_chains('AAPL', '2024-01-19')
            mock_make_request.assert_called_once_with(
                'markets/options/chains',
                {'symbol': 'AAPL', 'expiration': '2024-01-19', 'greeks': 'false'}
            )

    def test_get_balances(self):
        """Test get_balances."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            self.api.get_balances('acc123')
            mock_make_request.assert_called_once_with('accounts/acc123/balances')

    def test_get_positions(self):
        """Test get_positions."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            self.api.get_positions('acc123')
            mock_make_request.assert_called_once_with('accounts/acc123/positions')

    def test_get_orders(self):
        """Test get_orders."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            self.api.get_orders('acc123')
            mock_make_request.assert_called_once_with('accounts/acc123/orders')

class TestTradierAPIPlaceOrder(unittest.TestCase):
    def setUp(self):
        # Initialize TradierAPI with dummy values
        self.api = TradierAPI(access_token='fake_token', base_url='https://api.tradier.com/v1')

    def test_place_order_equity(self):
        """Test place_order for a standard equity order."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            order_data = {'class': 'equity', 'symbol': 'SPY', 'side': 'buy', 'quantity': 1, 'type': 'market', 'duration': 'day'}
            self.api.place_order('test_account_123', order_data)

            mock_make_request.assert_called_once_with(
                'accounts/test_account_123/orders',
                params=order_data,
                method='POST'
            )

    def test_place_order_options(self):
        """Test place_order for an options order."""
        with patch.object(TradierAPI, '_make_request') as mock_make_request:
            order_data = {'class': 'option', 'symbol': 'SPY', 'option_symbol': 'SPY240119C00400000', 'side': 'buy_to_open', 'quantity': 1, 'type': 'market', 'duration': 'day'}
            self.api.place_order('test_account_123', order_data)

            mock_make_request.assert_called_once_with(
                'accounts/test_account_123/orders',
                params=order_data,
                method='POST'
            )


class TestTradierAPIMakeRequest(unittest.TestCase):
    def setUp(self):
        self.api = TradierAPI(access_token='fake_token', base_url='https://api.tradier.com/v1')

    @patch('tradier_api.requests.get')
    def test_make_request_get_success(self, mock_get):
        """Test _make_request with GET method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': 'test_get'}
        mock_get.return_value = mock_response

        params = {'key': 'value'}
        result = self.api._make_request('test/endpoint', params=params, method='GET')

        mock_get.assert_called_once_with(
            'https://api.tradier.com/v1/test/endpoint',
            headers=self.api.headers,
            params=params
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(result, {'data': 'test_get'})

    @patch('tradier_api.requests.post')
    def test_make_request_post_success(self, mock_post):
        """Test _make_request with POST method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'data': 'test_post'}
        mock_post.return_value = mock_response

        params = {'key': 'value'}
        result = self.api._make_request('test/endpoint', params=params, method='POST')

        mock_post.assert_called_once_with(
            'https://api.tradier.com/v1/test/endpoint',
            headers=self.api.headers,
            data=params
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(result, {'data': 'test_post'})

    @patch('tradier_api.requests.get')
    def test_make_request_exception(self, mock_get):
        """Test _make_request exception handling."""
        mock_get.side_effect = requests.exceptions.RequestException("Mocked exception")

        result = self.api._make_request('test/endpoint', method='GET')

        mock_get.assert_called_once_with(
            'https://api.tradier.com/v1/test/endpoint',
            headers=self.api.headers,
            params=None
        )
        self.assertIsNone(result)

    @patch('tradier_api.requests.get')
    def test_make_request_http_error(self, mock_get):
        """Test _make_request HTTPError handling from raise_for_status."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Mocked HTTP Error")
        mock_get.return_value = mock_response

        result = self.api._make_request('test/endpoint', method='GET')

        mock_get.assert_called_once_with(
            'https://api.tradier.com/v1/test/endpoint',
            headers=self.api.headers,
            params=None
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertIsNone(result)

    def test_make_request_unsupported_method(self):
        """Test _make_request raises ValueError for unsupported HTTP methods."""
        with self.assertRaises(ValueError) as context:
            self.api._make_request('test/endpoint', method='PUT')
        self.assertEqual(str(context.exception), "Unsupported HTTP method: PUT")

class TestTradierAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.api = TradierAPI(access_token='fake_token', base_url='https://api.tradier.com/v1')

    @patch.object(TradierAPI, '_make_request')
    def test_get_history(self, mock_make_request):
        self.api.get_history('AAPL', interval='weekly', start='2023-01-01', end='2023-12-31')
        mock_make_request.assert_called_once_with(
            'markets/history',
            {'symbol': 'AAPL', 'interval': 'weekly', 'start': '2023-01-01', 'end': '2023-12-31'}
        )

    @patch.object(TradierAPI, '_make_request')
    def test_get_history_defaults(self, mock_make_request):
        self.api.get_history('AAPL')
        mock_make_request.assert_called_once_with(
            'markets/history',
            {'symbol': 'AAPL', 'interval': 'daily'}
        )

    @patch.object(TradierAPI, '_make_request')
    def test_get_option_chains(self, mock_make_request):
        self.api.get_option_chains('AAPL', '2024-01-19')
        mock_make_request.assert_called_once_with(
            'markets/options/chains',
            {'symbol': 'AAPL', 'expiration': '2024-01-19', 'greeks': 'false'}
        )

    @patch.object(TradierAPI, '_make_request')
    def test_get_balances(self, mock_make_request):
        self.api.get_balances('acc123')
        mock_make_request.assert_called_once_with('accounts/acc123/balances')

    @patch.object(TradierAPI, '_make_request')
    def test_get_positions(self, mock_make_request):
        self.api.get_positions('acc123')
        mock_make_request.assert_called_once_with('accounts/acc123/positions')

    @patch.object(TradierAPI, '_make_request')
    def test_get_orders(self, mock_make_request):
        self.api.get_orders('acc123')
        mock_make_request.assert_called_once_with('accounts/acc123/orders')

if __name__ == '__main__':
    unittest.main()
