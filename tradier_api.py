import requests
from config import Config

class TradierAPI:
    def __init__(self, access_token=Config.TRADIER_ACCESS_TOKEN, base_url=Config.TRADIER_API_BASE_URL):
        self.access_token = access_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        })

    def _make_request(self, endpoint, params=None, method='GET'):
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == 'GET':
                response = self.session.get(url, params=params)
            elif method == 'POST':
                response = self.session.post(url, data=params) # Use data for form-encoded
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            return None

    def get_quotes(self, symbols):
        """Fetches quotes for given symbols."""
        if symbols is None:
            return None
        if not isinstance(symbols, list):
            symbols = [symbols]
        if not symbols:
            return None
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