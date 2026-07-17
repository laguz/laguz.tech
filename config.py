# config.py
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application. "
                         "Please set the SECRET_KEY environment variable.")

    MONGO_URI = os.environ.get('MONGO_URI')
    if not MONGO_URI:
        raise ValueError("No MONGO_URI set for MongoDB connection. "
                         "Please set the MONGO_URI environment variable.")

    TRADIER_API_BASE_URL = "https://sandbox.tradier.com/v1" # Use sandbox for development
    TRADIER_ACCESS_TOKEN = os.environ.get('TRADIER_ACCESS_TOKEN')
    TRADIER_ACCOUNT_ID = os.environ.get('TRADIER_ACCOUNT_ID')
    TRADIER_LIVE_TRADING = os.environ.get('TRADIER_LIVE_TRADING', 'False').lower() in ['true', '1', 't']
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 't']
