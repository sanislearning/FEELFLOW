import numpy as np
import pandas as pd
import joblib
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from scipy.special import softmax
import urllib.request
import csv
from db_utils import getmarks, get_diary_entries, get_mood_ratings
from sklearn.linear_model import LinearRegression
# Load models once (reduces lag)
model = joblib.load("feelflow_rf_model.pkl")

# Load sentiment analysis model once
task = "sentiment"
MODEL = f"cardiffnlp/twitter-roberta-base-{task}"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
sentiment_model = AutoModelForSequenceClassification.from_pretrained(MODEL)

# Fetch sentiment labels only once
labels = []
mapping_link = f"https://raw.githubusercontent.com/cardiffnlp/tweeteval/main/datasets/{task}/mapping.txt"
with urllib.request.urlopen(mapping_link) as f:
    html = f.read().decode("utf-8").split("\n")
    csvreader = csv.reader(html, delimiter="\t")
    labels = [row[1] for row in csvreader if len(row) > 1]

def academic_trend_score(marks):
    if len(marks) < 2:
        return 0  
    recent_marks = marks[-4:]  
    X = np.arange(len(recent_marks)).reshape(-1, 1)
    Y = np.array(recent_marks)
    amodel = LinearRegression()
    amodel.fit(X, Y)
    slope = amodel.coef_[0]
    return max(-1, min(1, slope / 0.5))  

def get_weekly_average(daily_ratings, default=7):
    if len(daily_ratings) < 7:
        return 7  
    return np.mean(daily_ratings[-7:])

def get_sentiment_probabilities(text, default="I had a normal day today"):
    if not text:
        text = default  # Use the default text when input is missing
    encoded_input = tokenizer(text, return_tensors="pt", padding=True)
    output = sentiment_model(**encoded_input)
    scores = softmax(output[0][0].detach().numpy())
    return {label: scores[i] for i, label in enumerate(labels)}


from db_utils import send_alert_email  # We will create this function next
from db_utils import get_guardian_email  # Make sure you have this function

def predict_mental_health(username):
    marks = getmarks(username)
    diary = get_diary_entries(username)
    mood = get_mood_ratings(username)

    academic_trend = academic_trend_score(marks)
    weekly_avg_rating = get_weekly_average(mood)
    sentiment_probs = get_sentiment_probabilities(diary)

    input_features = pd.DataFrame([[academic_trend, weekly_avg_rating, 
                                    sentiment_probs["negative"], sentiment_probs["neutral"], sentiment_probs["positive"]]],  
                                  columns=["academic_trend", "weekly_average_rating", "negative_prob", "neutral_prob", "positive_prob"])

    prediction = model.predict(input_features)[0]

    # If prediction is negative, send an alert
    if prediction < 0.1:  # Adjust the threshold if needed
        guardian_email = get_guardian_email(username)  # Fetch guardian's email
        send_alert_email(username, guardian_email)

    return (prediction,
            marks,
            diary, 
            mood, 
            academic_trend, 
            weekly_avg_rating, 
            sentiment_probs
            )

