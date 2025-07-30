import requests
import json
from config import Config

class TradierAPI:
    def __init__(self, access_token=Config.TRADIER_ACCESS_TOKEN, base_url=Config.TRADIER_BASE_URL):
        self.access_token = access_token
        self.base_url = base_url
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

    def _make_request(self, endpoint, params=None, method='GET'):
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, data=params) # Use data for form-encoded
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            return None

    def get_quotes(self, symbols):
        """Fetches quotes for given symbols."""
        if not isinstance(symbols, list):
            symbols = [symbols]
        params = {'symbols': ','.join(symbols), 'greeks': 'false'} # Add Greeks for options if needed
        return self._make_request('markets/quotes', params)

    def get_history(self, symbol, interval='daily', start=None, end=None):
        """Fetches historical data for a symbol."""
        params = {'symbol': symbol, 'interval': interval}
        if start:
            params['start'] = start # Format YYYY-MM-DD
        if end:
            params['end'] = end # Format YYYY-MM-DD
        return self._make_request('markets/history', params)

    def get_option_chains(self, symbol, expiration):
        """Fetches option chain for a symbol and expiration."""
        params = {'symbol': symbol, 'expiration': expiration, 'greeks': 'false'}
        return self._make_request('markets/options/chains', params)

    def get_balances(self, account_id):
        """Fetches account balances."""
        return self._make_request(f'accounts/{account_id}/balances')

    def get_positions(self, account_id):
        """Fetches current positions."""
        return self._make_request(f'accounts/{account_id}/positions')

    def get_orders(self, account_id):
        """Fetches order history."""
        return self._make_request(f'accounts/{account_id}/orders')

    def place_order(self, account_id, order_data):
        """
        Places a trading order.
        order_data should be a dictionary with parameters like:
        {'class': 'equity', 'symbol': 'SPY', 'side': 'buy', 'quantity': 1, 'type': 'market', 'duration': 'day'}
        For options, include 'option_symbol'.
        """
        return self._make_request(f'accounts/{account_id}/orders', params=order_data, method='POST')

    # Add more API methods as needed (e.g., streaming, corporate actions)

# Example usage (for testing)
if __name__ == '__main__':
    api = TradierAPI()
    # Test getting quotes
    # quotes = api.get_quotes(['SPY', 'AAPL'])
    # if quotes and 'quotes' in quotes and quotes['quotes'] is not None:
    #     for quote in quotes['quotes']['quote']:
    #         print(f"Symbol: {quote['symbol']}, Last: {quote['last']}")
    # else:
    #     print("Could not retrieve quotes.")

    # Test getting historical data
    # history = api.get_history('AAPL', interval='daily', start='2024-01-01', end='2024-01-31')
    # if history and 'history' in history and history['history'] is not None:
    #     for day in history['history']['day']:
    #         print(f"Date: {day['date']}, Close: {day['close']}")
    # else:
    #     print("Could not retrieve historical data.")