# Create a new session, credentials path is required.
import os
from dotenv import load_dotenv, find_dotenv
from td.client import TDClient
load_dotenv(find_dotenv())
client_id = os.environ.get("client_id")

TDSession = TDClient(
    client_id,
    redirect_uri='http://localhost',
    credentials_path='/content/credentials.json'
)

# Login to the session
TDSession.login()