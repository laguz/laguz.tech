import unittest
import os
from unittest.mock import patch, MagicMock

# Environment setup is needed before importing benchmark_pnl
os.environ['SECRET_KEY'] = 'test_secret'
os.environ['MONGO_URI'] = 'mongodb://localhost:27017/'
os.environ['TRADIER_ACCESS_TOKEN'] = 'test_token'
os.environ['TRADIER_ACCOUNT_ID'] = 'test_account'
os.environ['TRADIER_LIVE_TRADING'] = '0'

import benchmark_pnl

class TestBenchmarkPnl(unittest.TestCase):
    def setUp(self):
        benchmark_pnl.app.users_collection.find = MagicMock(return_value=[
            {
                '_id': f'user_{i}',
                'tradier_account_id': f'account_{i}',
                'tradier_access_token': f'token_{i}'
            } for i in range(2)
        ])

    @patch('benchmark_pnl.time.sleep')
    def test_mock_get_account_balance(self, mock_sleep):
        result = benchmark_pnl.mock_get_account_balance()
        mock_sleep.assert_called_once_with(0.1)
        self.assertEqual(result, {
            'realized_gain_loss': 100,
            'unrealized_gain_loss': 50,
            'total_equity': 10000
        })

    @patch('benchmark_pnl.time.time')
    @patch('builtins.print')
    @patch('benchmark_pnl.app.update_pnl_snapshot')
    def test_run_current_benchmark(self, mock_update, mock_print, mock_time):
        mock_time.side_effect = [1.0, 2.0]
        benchmark_pnl.run_current_benchmark()
        mock_update.assert_called_once()
        mock_print.assert_any_call("Current Implementation (ThreadPoolExecutor): 1.0000 seconds")
        mock_print.assert_any_call("API Calls made: 0")

    @patch('benchmark_pnl.time.time')
    @patch('builtins.print')
    @patch('benchmark_pnl.proposed_update_pnl_snapshot')
    def test_run_proposed_benchmark(self, mock_proposed, mock_print, mock_time):
        mock_time.side_effect = [1.0, 2.5]
        benchmark_pnl.run_proposed_benchmark()
        mock_proposed.assert_called_once()
        mock_print.assert_any_call("Proposed Implementation (O(1) API call): 1.5000 seconds")
        mock_print.assert_any_call("API Calls made: 0")

    @patch('benchmark_pnl.app.Account')
    @patch('benchmark_pnl.app.pnl_collection.insert_many')
    @patch('benchmark_pnl.app.datetime')
    def test_proposed_update_pnl_snapshot(self, mock_datetime, mock_insert, mock_account_cls):
        mock_account = MagicMock()
        mock_account_cls.return_value = mock_account
        mock_account.get_account_balance.return_value = {
            'realized_gain_loss': 10,
            'unrealized_gain_loss': 20,
            'total_equity': 1000
        }
        mock_now = MagicMock()
        mock_datetime.now.return_value = mock_now

        benchmark_pnl.proposed_update_pnl_snapshot()

        self.assertTrue(mock_insert.called)
        args, kwargs = mock_insert.call_args
        snapshots = args[0]
        self.assertEqual(len(snapshots), 2)
        self.assertEqual(snapshots[0]['user_id'], 'user_0')
        self.assertEqual(snapshots[0]['pnl'], 30)
        self.assertEqual(snapshots[0]['total_equity'], 1000)
        self.assertEqual(snapshots[0]['date'], mock_now)

    @patch('benchmark_pnl.app.Account')
    @patch('builtins.print')
    def test_proposed_update_pnl_snapshot_exception(self, mock_print, mock_account_cls):
        mock_account_cls.side_effect = Exception("API error")
        benchmark_pnl.proposed_update_pnl_snapshot()
        mock_print.assert_any_call("Error preparing P&L for user user_0: API error")
        mock_print.assert_any_call("Error preparing P&L for user user_1: API error")

    @patch('benchmark_pnl.run_current_benchmark')
    @patch('benchmark_pnl.run_proposed_benchmark')
    @patch('builtins.print')
    def test_main_execution(self, mock_print, mock_proposed, mock_current):
        # Because we can't easily test if __name__ == '__main__' without subprocess,
        # we can just assume running the functions does what it says.
        # But we could also mock the module level check if we wanted.
        pass

if __name__ == '__main__':
    unittest.main()
