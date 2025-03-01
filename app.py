from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')  # This renders the index page

@app.route('/login', methods=['GET', 'POST'])  # Handling both GET and POST for login
def login():
    if request.method == 'POST':
        # Add logic for authentication here if you need to handle login submissions
        username = request.form['username']
        password = request.form['password']
        print(f"Username: {username}, Password: {password}")  # Debugging log
        return redirect(url_for('index'))  # Redirect to the index page after login
    return render_template('login.html')  # Renders the login page when accessed with GET
    
if __name__ == '__main__':
    app.run(debug=True)
