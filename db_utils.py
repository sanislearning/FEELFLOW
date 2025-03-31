# db_utils.py
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

    


def get_marks(username):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    query = "SELECT sgpa, date FROM academic WHERE username = ? ORDER BY date"
    cursor.execute(query, (username,))

    marks = [{"sgpa": row[0], "date": row[1]} for row in cursor.fetchall()]
    
    conn.close()
    return marks

