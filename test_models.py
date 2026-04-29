import unittest
from models import Trade, get_trades_data

class TestTrade(unittest.TestCase):
    def test_positive_pnl(self):
        trade = Trade("AAPL", 10, 150.00, 155.50)
        self.assertEqual(trade.pnl, 55.0)

    def test_negative_pnl(self):
        trade = Trade("MSFT", 5, 280.50, 275.25)
        self.assertEqual(trade.pnl, -26.25)

    def test_zero_pnl(self):
        trade = Trade("GOOG", 2, 1200.00, 1200.00)
        self.assertEqual(trade.pnl, 0.0)

class TestModels(unittest.TestCase):
    def test_get_trades_data(self):
        trades, total_pnl = get_trades_data()

        # Added per issue: verify the length of trades is exactly 4
        self.assertEqual(len(trades), 4)

        # Verify total P&L calculation directly in loop instead of just hardcoded value
        calculated_total_pnl = sum(trade.pnl for trade in trades)
        self.assertEqual(total_pnl, calculated_total_pnl)

        self.assertIsInstance(trades[0], Trade)

        self.assertEqual(trades[0].symbol, "AAPL")
        self.assertEqual(trades[0].pnl, 55.0)

        self.assertEqual(trades[1].symbol, "MSFT")
        self.assertEqual(trades[1].pnl, -26.25)

        self.assertEqual(trades[2].symbol, "GOOG")
        self.assertEqual(trades[2].pnl, 30.0)

        self.assertEqual(trades[3].symbol, "TSLA")
        self.assertEqual(trades[3].pnl, -15.0)

        self.assertEqual(total_pnl, 43.75)

if __name__ == '__main__':
    unittest.main()
