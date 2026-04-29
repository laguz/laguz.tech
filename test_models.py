import unittest
from models import Trade, get_trades_data

class TestModels(unittest.TestCase):
    def test_trade_init(self):
        # Happy path - Positive P&L
        trade_positive = Trade("AAPL", 10, 100.0, 150.0)
        self.assertEqual(trade_positive.symbol, "AAPL")
        self.assertEqual(trade_positive.quantity, 10)
        self.assertEqual(trade_positive.buy_price, 100.0)
        self.assertEqual(trade_positive.sell_price, 150.0)
        self.assertEqual(trade_positive.pnl, 500.0)

        # Negative P&L
        trade_negative = Trade("MSFT", 5, 200.0, 150.0)
        self.assertEqual(trade_negative.pnl, -250.0)

        # Zero P&L
        trade_zero = Trade("GOOG", 2, 100.0, 100.0)
        self.assertEqual(trade_zero.pnl, 0.0)

        # Rounding behavior
        trade_rounding = Trade("TSLA", 3, 100.123, 100.456)
        # (100.456 - 100.123) = 0.333 * 3 = 0.999 -> rounds to 1.0
        self.assertEqual(trade_rounding.pnl, 1.0)

        # Rounding down
        trade_rounding2 = Trade("AMZN", 1, 100.0, 100.1234)
        # (100.1234 - 100.0) = 0.1234 -> rounds to 0.12
        self.assertEqual(trade_rounding2.pnl, 0.12)

    def test_get_trades_data(self):
        trades, total_pnl = get_trades_data()

        self.assertEqual(len(trades), 4)
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
