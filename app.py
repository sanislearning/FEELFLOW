from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask import flash
from flask_migrate import Migrate
import sqlite3

db_path = r"C:\Users\HP\Documents\Projects\FEELFLOW\instance\users.db"

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def setpassword(self, password):
        self.password_hash = generate_password_hash(password)

    def checkpassword(self, password):
        return check_password_hash(self.password_hash, password)  # Use self.password_hash instead of self.password

class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    mood = db.Column(db.Integer, nullable=False)
    diary_entry = db.Column(db.Text, nullable=True)  # New column for journal entry

    __table_args__ = (db.UniqueConstraint('username', 'date', name='unique_user_date'),)


class Academic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    marks = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('index.html')  # This renders the index page


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.checkpassword(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "error")  # Flash error message
            return redirect(url_for('login'))  # Redirect instead of re-rendering

    return render_template('login.html')  
  # Renders the login page when accessed with GET
# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    user = session['username']
    today = datetime.utcnow().date()
    
    # Check if mood entry exists for today
    existing_mood = Mood.query.filter_by(username=user, date=today).first()
    
    if not existing_mood:
        return redirect(url_for('mood_rating'))  # Redirect to mood entry page if missing
    
    return render_template('dashboard.html', username=user)



# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user:
            flash("User already exists! Please sign in.", "error")  # Flash alert
            return redirect(url_for('login'))  # Redirect to login
        
        else:
            new_user = User(username=username)
            new_user.setpassword(password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")  # Flash alert
            return redirect(url_for('index'))  # Redirect to index

    return render_template('register.html')

  # Return register page for GET requests

# LOGOUT
@app.route('/logout')
def logout():
    if "username" in session:
        session.pop('username', None)
        return redirect(url_for('index'))
    

@app.route('/mood_rating', methods=['GET', 'POST'])
def mood_rating():
    if 'username' not in session:
        return redirect(url_for('index'))  # If not logged in, go to home

    if request.method == 'POST':
        mood = request.form['mood']
        today = datetime.utcnow().date()

        # Check if the user has already submitted a mood today
        existing_mood = Mood.query.filter_by(username=session['username'], date=today).first()
        if not existing_mood:
            new_mood = Mood(username=session['username'], date=today, mood=mood)
            db.session.add(new_mood)
        else:
            existing_mood.mood = mood  # **Update existing mood**
        
        db.session.commit()
        return redirect(url_for('dashboard'))  # Redirect to dashboard after submitting

    return render_template('moodrating.html')  # **Always show the page**



@app.route('/journal', methods=['GET'])
def journal():
    if "username" not in session:
        return redirect(url_for("index"))

    user = session["username"]

    # Fetch login dates for the current user
    logged_in_dates = [
        entry.date.strftime("%Y-%m-%d") for entry in Mood.query.filter_by(username=user).all()
    ]
    return render_template("journal.html", logged_in_dates=logged_in_dates)




@app.route('/save_entry', methods=['POST'])
def save_entry():
    if 'username' not in session:
        return jsonify({"success": False, "message": "User not logged in"}), 401

    data = request.get_json()
    entry_text = data.get("entry")
    today = datetime.utcnow().date()
    user = session["username"]

    # Check if there's already an entry for today
    mood_entry = Mood.query.filter_by(username=user, date=today).first()

    if mood_entry:
        if mood_entry.diary_entry is None:
            mood_entry.diary_entry = entry_text  # Set it to the new entry instead of trying +=
        else:
            mood_entry.diary_entry += f"\n{entry_text}"  # Append if it's not None

    db.session.commit()
    return jsonify({"success": True, "message": "Diary entry saved!"})




@app.route('/academic', methods=['GET', 'POST'])
def academic():
    if 'username' not in session:
        return redirect(url_for('index'))

    user = session['username']

    if request.method == 'POST':
        subject = request.form.get('subject')
        marks = request.form.get('marks')

        if not subject or not marks.isdigit():
            # flash("Invalid input. Please enter a valid subject and marks.", "error")
            return redirect(url_for('academic'))

        marks = int(marks)  # Convert to integer
        today = datetime.utcnow().date()  # Get today's date

        # Check if an entry already exists for this subject and date
        existing_entry = Academic.query.filter_by(username=user, subject=subject, date=today).first()

        if existing_entry:
            existing_entry.marks = marks  # Update marks
        else:
            new_entry = Academic(username=user, subject=subject, marks=marks, date=today)
            db.session.add(new_entry)

        db.session.commit()
        # flash("Marks updated successfully!" if existing_entry else "Marks added successfully!", "success")
        return redirect(url_for('academic'))

    return render_template('academic.html')

from db_utils import get_marks

@app.route('/get_marks', methods=['GET'])
def get_marks_data():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = session['username']
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all subjects for the user
    cursor.execute("SELECT DISTINCT subject FROM academic WHERE username = ?", (user,))
    subjects = [row[0] for row in cursor.fetchall()]
    
    conn.close()

    # Fetch marks for each subject
    data = {subject: get_marks(user, subject) for subject in subjects}

    return jsonify(data)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
