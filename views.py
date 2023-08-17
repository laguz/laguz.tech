from app import app

@app.route('/') 
def homepage(): 
    return ("Home Page")