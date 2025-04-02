from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask import flash
from flask_migrate import Migrate
import sqlite3, requests
from db_utils import get_marks, send_alert_email, get_guardian_email
from dotenv import load_dotenv
from flask_mail import Mail,Message
import os
from model import predict_mental_health



db_path = r"C:\Users\HP\Documents\Projects\FEELFLOW\instance\users.db"

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')  # Store in environment variable
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')  # Store in environment variable

mail = Mail(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)



API_KEY = "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"  # Replace with your actual API key
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Predefined system message to set Lumi's context
SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are Lumi, a supportive companion for people to talk to. "
        "You will listen and provide advice in a clear and concise manner. "
        "Your responses should be friendly, empathetic, and restricted to around two paragraphs in length."
        "If a response can be made in a single paragraph, do so."
    )
}

# Store conversation history
conversation_history = [SYSTEM_MESSAGE]


def chat_with_groq(user_message):
    global conversation_history

    # Append user's message to conversation history
    conversation_history.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": conversation_history
    }

    response = requests.post(API_URL, headers=headers, json=data)

    if response.status_code == 200:
        bot_response = response.json()["choices"][0]["message"]["content"]
        
        # Store Lumi's response in conversation history
        conversation_history.append({"role": "assistant", "content": bot_response})
        
        return bot_response
    else:
        return f"Error: {response.status_code}, {response.text}"



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Unique
    trusted_email = db.Column(db.String(120), nullable=False)  # Not unique
    phone = db.Column(db.String(15), nullable=False)  # not Unique


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
    sgpa = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)


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
        email = request.form['email']
        trusted_email = request.form['trusted_email']
        phone = request.form.get('phone')  # Optional field

        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            flash("Username or email already exists! Please sign in.", "error")
            return redirect(url_for('login'))

        # Create new user
        new_user = User(username=username, email=email, trusted_email=trusted_email, phone=phone)
        new_user.setpassword(password)
        
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('index'))

    return render_template('register.html')




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
    predict_mental_health('username')
    return jsonify({"success": True, "message": "Diary entry saved!"})



@app.route('/academic', methods=['GET', 'POST'])
def academic():
    if 'username' not in session:
        return redirect(url_for('index'))

    user = session['username']

    if request.method == 'POST':
        sgpa = request.form.get('sgpa')
        date_str = request.form.get('date')  # Get date as a string

        if not sgpa or not date_str:
            return redirect(url_for('academic'))

        sgpa = float(sgpa)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()  # Convert string to date

        new_entry = Academic(username=user, sgpa=sgpa, date=date_obj)
        db.session.add(new_entry)
        db.session.commit()

        return redirect(url_for('academic'))

    return render_template('academic.html')






@app.route('/get_marks', methods=['GET'])
def get_marks_data():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user = session['username']
    return jsonify(get_marks(user))



@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')


@app.route('/send-test-mail')
def send_test_mail():
    try:
        msg = Message(
            subject="Feelflow Test Email",
            sender=os.getenv('EMAIL_USER'),
            recipients=["jesterjuice18@gmail.com"],  # Replace with your test recipient
            body="This is a test email from Feelflow!"
        )
        mail.send(msg)
        send_alert_email('username', get_guardian_email('username'))
        return "Email sent successfully!"
    except Exception as e:
        return f"Error: {e}"




@app.route('/chat', methods=['GET','POST'])
def chat():
    user_message = request.form['message']
    bot_response = chat_with_groq(user_message)
    return jsonify({"response": bot_response})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
