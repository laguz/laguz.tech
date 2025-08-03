# config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here' # Change this in production
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/investment_db'
    TRADIER_API_BASE_URL = "https://sandbox.tradier.com/v1" # Use sandbox for development
    TRADIER_ACCESS_TOKEN = os.environ.get('TRADIER_ACCESS_TOKEN')
    TRADIER_ACCOUNT_ID = os.environ.get('TRADIER_ACCOUNT_ID')
    TRADIER_LIVE_TRADING = os.environ.get('TRADIER_LIVE_TRADING')