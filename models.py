# models.py

class Trade:
    """Represents a single trade with P&L calculation."""
    def __init__(self, symbol, quantity, buy_price, sell_price):
        self.symbol = symbol
        self.quantity = quantity
        self.buy_price = buy_price
        self.sell_price = sell_price
        self.pnl = round((self.sell_price - self.buy_price) * self.quantity, 2)

def get_trades_data():
    """Fetches a list of mock trade objects and calculates total P&L."""
    trades = [
        Trade("AAPL", 10, 150.00, 155.50),
        Trade("MSFT", 5, 280.50, 275.25),
        Trade("GOOG", 2, 1200.00, 1215.00),
        Trade("TSLA", 3, 850.00, 845.00)
    ]
    
    total_pnl = sum(trade.pnl for trade in trades)
    
    return trades, round(total_pnl, 2)