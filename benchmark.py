import time
import os
import sys
from unittest.mock import MagicMock

# Mock dotenv before importing config
sys.modules['dotenv'] = MagicMock()

os.environ['SECRET_KEY'] = '1'
os.environ['MONGO_URI'] = '1'
os.environ['TRADIER_ACCESS_TOKEN'] = '1'
os.environ['TRADIER_ACCOUNT_ID'] = '1'
os.environ['TRADIER_LIVE_TRADING'] = '0'

from tradier_api import TradierAPI

class DummyAPI(TradierAPI):
    def __init__(self):
        super().__init__(access_token="DUMMY", base_url="https://httpbin.org/anything")

def run_benchmark():
    api = DummyAPI()

    start_time = time.time()
    for _ in range(10):
        # httpbin.org/anything/test will just echo
        api._make_request('test')
    end_time = time.time()

    print(f"Time taken for 10 requests: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    run_benchmark()
