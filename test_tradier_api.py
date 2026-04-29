import sys
from unittest.mock import MagicMock, patch

# Mock dependencies before import because they are not installed in this environment.
# In a real CI environment, these should be installed via pip.
if 'requests' not in sys.modules:
    sys.modules['requests'] = MagicMock()
if 'dotenv' not in sys.modules:
    sys.modules['dotenv'] = MagicMock()

import unittest
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


if __name__ == '__main__':
    unittest.main()
