from flask_mail import Message
import sqlite3  
db_path = r"C:\Users\HP\Documents\Projects\FEELFLOW\instance\users.db"


def get_mood_ratings(username):
    moods = []

    # Connect to the database using the absolute path
    conn = sqlite3.connect(db_path)  
    cursor = conn.cursor()
    
    query = "SELECT * FROM mood WHERE username = ?"
    cursor.execute(query, (username,))

    rows = cursor.fetchall()
    for row in rows:
        moods.append(row[3])

    conn.close()
    return moods


def get_diary_entries(username):
    diary = []

    # Connect to the database using the absolute path
    conn = sqlite3.connect(db_path)  
    cursor = conn.cursor()
    
    query = "SELECT * FROM mood WHERE username = ?"
    cursor.execute(query, (username,))

    rows = cursor.fetchall()
    for row in rows:
        diary.append(row[4])

    return diary if diary else None

def getmarks(username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT sgpa, date FROM academic WHERE username = ?"
    cursor.execute(query, (username,))

    rows = cursor.fetchall()
    marks = []
    for row in rows:
        marks.append(row[0])
    return marks


def get_marks(username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = "SELECT sgpa, date FROM academic WHERE username = ? ORDER BY date"
    cursor.execute(query, (username,))

    marks = [{"sgpa": row[0], "date": row[1]} for row in cursor.fetchall()]
    
    conn.close()
    return marks


def get_guardian_email(username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = "SELECT trusted_email FROM user WHERE username = ?"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    conn.close()  # Close the connection
    return result[0]


  # Import the mail instance from your Flask app

def send_alert_email(username, guardian_email):
    """Sends an alert email to the guardian if the mental health score indicates concern."""
    print("send_alert_email function called!")

    from app import mail
    subject = "Urgent: Mental Health Alert for Your Ward"
    body = f"""Dear Guardian,\n\n
    Our system has detected a concerning pattern in {username}'s recent mental health indicators. 
    We recommend checking in on them and offering support if needed.\n\n
    Best,\nFeelFlow Team"""

    msg = Message(subject, recipients=[guardian_email], body=body)
    
    try:
        mail.send(msg)
        print("send_alert_email function called! in try block")

        print(f"Alert email sent to {guardian_email} for {username}.")
    except Exception as e:
        print(f"Failed to send alert email: {e}")
