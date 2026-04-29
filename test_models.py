import unittest
from models import Trade, get_trades_data

class TestModels(unittest.TestCase):
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
