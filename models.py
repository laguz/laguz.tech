# models.py

class Trade:
    """Represents a single trade with P&L calculation."""
    def __init__(self, symbol, quantity, buy_price, sell_price):
        self.symbol = symbol
        self.quantity = quantity
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.pnl = round((self.sell_price - self.buy_price) * self.quantity, 2)