from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure database (SQLite for now)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///moods.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)




# Define Mood model

class Mood(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to user
    user = db.relationship('User', backref='moods')  # Create relationship with User model

# Create database
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    moods = Mood.query.order_by(Mood.date.desc()).all()
    print(f"Retrieved moods: {moods}")  # Debugging log
    return render_template('index.html', moods=moods)

@app.route('/add_mood', methods=['POST'])
@app.route('/add_mood', methods=['POST'])
def add_mood():
    mood_rating = request.form['mood_rating']
    emoji = request.form['emoji']
    new_mood = Mood(rating=mood_rating, emoji=emoji)
    db.session.add(new_mood)
    db.session.commit()  # Make sure this is here to commit the changes to the database
    return redirect('/')


@app.route('/submit_mood', methods=['POST'])
def submit_mood():
    rating = request.json.get('rating')
    print(f"Received rating via AJAX: {rating}")  # Debugging log
    if rating is not None:
        new_mood = Mood(rating=rating)
        db.session.add(new_mood)
        db.session.commit()
        return jsonify({'message': 'Mood rating saved!'}), 200
    return jsonify({'error': 'Invalid rating'}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # In a future step, we'll verify the credentials
        username = request.form['username']
        password = request.form['password']
        print(f"Username: {username}, Password: {password}")  # Debugging log
        return redirect(url_for('home'))
    return render_template('login.html')



if __name__ == '__main__':
    app.run(debug=True)
