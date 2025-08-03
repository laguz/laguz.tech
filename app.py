# app.py
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
# For password hashing (CRUCIAL for security!)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- MongoDB Configuration ---
#MONGO_URI = "mongodb://localhost:27017/"
MONGO_URI = "mongodb+srv://laguz:ujl6UHFEFXShdJWK@tradingbot.scvgoqu.mongodb.net/?retryWrites=true&w=majority&appName=TradingBot"
DATABASE_NAME = "accounts"
#COLLECTION_NAME = "users"

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
#users_collection = db[COLLECTION_NAME]


@app.route('/')
def index():
    return "Hello, visit /add to add a user."

@app.route('/add')
def add_user_form():
    return render_template('add_user.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password'] # This will be the plain text password

        # --- IMPORTANT SECURITY CONSIDERATION ---
        # NEVER store plain text passwords. Always hash them!
        hashed_password = generate_password_hash(password)

        # Create a document (Python dictionary) to insert into MongoDB
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password  # Store the hashed password
        }

        try:
            # Insert the document into the 'users' collection
            result = db.users.insert_one(user_data)
            print(f"User added with ID: {result.inserted_id}")
            return redirect(url_for('user_added_success'))
        except Exception as e:
            print(f"Error adding user: {e}")
            return "Error adding user."

@app.route('/user_added_success')
def user_added_success():
    return "User added successfully!"

# --- Run the app ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)