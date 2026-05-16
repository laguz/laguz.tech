import sys
from unittest.mock import MagicMock

# Mock dotenv before importing config
sys.modules['dotenv'] = MagicMock()

import unittest
import os
import importlib
from unittest.mock import patch

# Set dummy env vars for initial import
os.environ['SECRET_KEY'] = 'dummy'
os.environ['MONGO_URI'] = 'dummy'

import config

class TestConfig(unittest.TestCase):
    def setUp(self):
        # Save original environment to avoid side effects on other tests
        self.original_env = os.environ.copy()

    def tearDown(self):
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        # Reload config one last time with original env to keep it in a sane state
        importlib.reload(config)

    def test_secret_key_missing(self):
        # Use patch.dict with clear=True to ensure no env vars are present
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "No SECRET_KEY set"):
                importlib.reload(config)

    def test_mongo_uri_missing(self):
        # Set only SECRET_KEY
        with patch.dict(os.environ, {"SECRET_KEY": "test_secret"}, clear=True):
            with self.assertRaisesRegex(ValueError, "No MONGO_URI set"):
                importlib.reload(config)

    def test_config_success(self):
        # Set all required env vars
        env_vars = {
            "SECRET_KEY": "test_secret",
            "MONGO_URI": "mongodb://localhost:27017/test_db",
            "TRADIER_ACCESS_TOKEN": "test_token",
            "TRADIER_ACCOUNT_ID": "test_account",
            "TRADIER_LIVE_TRADING": "false",
            "FLASK_DEBUG": "True"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            importlib.reload(config)
            from config import Config
            self.assertEqual(Config.SECRET_KEY, "test_secret")
            self.assertEqual(Config.MONGO_URI, "mongodb://localhost:27017/test_db")
            self.assertEqual(Config.TRADIER_ACCESS_TOKEN, "test_token")
            self.assertEqual(Config.TRADIER_ACCOUNT_ID, "test_account")
            self.assertEqual(Config.TRADIER_LIVE_TRADING, "false")
            self.assertTrue(Config.DEBUG)

    def test_debug_parsing(self):
        # Test various values for FLASK_DEBUG
        test_cases = [
            ("True", True),
            ("true", True),
            ("1", True),
            ("t", True),
            ("False", False),
            ("false", False),
            ("0", False),
            ("random", False),
            ("", False)
        ]

        base_env = {
            "SECRET_KEY": "test_secret",
            "MONGO_URI": "mongodb://localhost:27017/test_db"
        }

        for val, expected in test_cases:
            env = base_env.copy()
            env["FLASK_DEBUG"] = val

            with patch.dict(os.environ, env, clear=True):
                importlib.reload(config)
                from config import Config
                self.assertEqual(Config.DEBUG, expected, f"Failed for FLASK_DEBUG='{val}'")

    def test_debug_missing(self):
        # Test default value when FLASK_DEBUG is missing
        base_env = {
            "SECRET_KEY": "test_secret",
            "MONGO_URI": "mongodb://localhost:27017/test_db"
        }
        with patch.dict(os.environ, base_env, clear=True):
            importlib.reload(config)
            from config import Config
            self.assertFalse(Config.DEBUG)

if __name__ == '__main__':
    unittest.main()
