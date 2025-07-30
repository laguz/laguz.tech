import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Config:
    TRADIER_ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")
    TRADIER_ACCESS_TOKEN = os.getenv("TRADIER_ACCESS_TOKEN")
# for Live Trading
    TRADIER_BASE_URL = "https://api.tradier.com/v1"
    TRADIER_STREAM_URL = "https://stream.tradier.com/v1"

# for Paper Trading
    TRADIER_PAPER_BASE_URL = "https://sandbox.tradier.com/v1"

    #Tradier_Api settings
    TRADIER_SANDBOX_TOKEN = os.getenv("TRADIER_SANDBOX_TOKEN")
    TRADIER_SANDBOX_ACCT = os.getenv("TRADIER_SANDBOX_ACCT")