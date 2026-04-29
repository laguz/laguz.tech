import unittest
from models import Trade

class TestModels(unittest.TestCase):
    def test_trade_init(self):
        """Test that Trade is initialized with correct attributes."""
        trade = Trade("AAPL", 10, 150.00, 155.50)
        self.assertEqual(trade.symbol, "AAPL")
        self.assertEqual(trade.quantity, 10)
        self.assertEqual(trade.buy_price, 150.00)
        self.assertEqual(trade.sell_price, 155.50)
        self.assertEqual(trade.pnl, 55.0)

        # Test with float quantity and negative prices if applicable or just another edge case
        trade2 = Trade("MSFT", 5.5, 100.0, 90.0)
        self.assertEqual(trade2.symbol, "MSFT")
        self.assertEqual(trade2.quantity, 5.5)
        self.assertEqual(trade2.buy_price, 100.0)
        self.assertEqual(trade2.sell_price, 90.0)
        self.assertEqual(trade2.pnl, -55.0)

    def test_trade_pnl_calculation(self):
        trade1 = Trade("AAPL", 10, 150.00, 155.50)
        self.assertEqual(trade1.symbol, "AAPL")
        self.assertEqual(trade1.pnl, 55.0)

        trade2 = Trade("MSFT", 5, 280.50, 275.25)
        self.assertEqual(trade2.symbol, "MSFT")
        self.assertEqual(trade2.pnl, -26.25)

        trade3 = Trade("GOOG", 2, 1200.00, 1215.00)
        self.assertEqual(trade3.symbol, "GOOG")
        self.assertEqual(trade3.pnl, 30.0)

        trade4 = Trade("TSLA", 3, 850.00, 845.00)
        self.assertEqual(trade4.symbol, "TSLA")
        self.assertEqual(trade4.pnl, -15.0)

if __name__ == '__main__':
    unittest.main()
