# app.py

from flask import Flask, render_template
from models import get_trades_data

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Renders the main financial dashboard page."""
    trades, total_pnl = get_trades_data()
    return render_template('dashboard.html', trades=trades, total_pnl=total_pnl)

if __name__ == '__main__':
    app.run(debug=True)