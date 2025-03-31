#final output script
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from scipy.special import softmax
import urllib.request
import csv

# Load trained model (ensure the model is trained before running this)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)  # Ensure X_train, y_train are defined

# Function to calculate academic trend score
def academic_trend_score(marks):
    if len(marks) < 2:
        return 0  # Neutral trend if not enough data

    recent_marks = marks[-4:]  # Use last 4 marks
    X = np.arange(len(recent_marks)).reshape(-1, 1)
    Y = np.array(recent_marks)

    # Fit Linear Regression model
    model = LinearRegression()
    model.fit(X, Y)

    # Normalize slope
    slope = model.coef_[0]
    max_slope = 0.5
    normalized_slope = max(-1, min(1, slope / max_slope))

    return normalized_slope

# Function to compute weekly average
def get_weekly_average(daily_ratings):
    if len(daily_ratings) < 7:
        return None  # Not enough data
    return np.mean(daily_ratings[-7:])

# Function for sentiment analysis


task = "sentiment"
MODEL = f"cardiffnlp/twitter-roberta-base-{task}"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
sentiment_model = AutoModelForSequenceClassification.from_pretrained(MODEL)

# Load sentiment labels
labels = []
mapping_link = f"https://raw.githubusercontent.com/cardiffnlp/tweeteval/main/datasets/{task}/mapping.txt"
with urllib.request.urlopen(mapping_link) as f:
    html = f.read().decode("utf-8").split("\n")
    csvreader = csv.reader(html, delimiter="\t")
    labels = [row[1] for row in csvreader if len(row) > 1]

def get_sentiment_probabilities(text):
    encoded_input = tokenizer(text, return_tensors="pt")
    output = sentiment_model(**encoded_input)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)  # Convert to probabilities

    return {
        "negative": scores[labels.index("negative")],
        "neutral": scores[labels.index("neutral")],
        "positive": scores[labels.index("positive")]
    }

# User Input Loop
while True:
    print("\n📝 Enter your data:")

    # User inputs academic marks
    marks = list(map(float, input("Enter your last 4 academic marks (comma-separated): ").split(",")))
    academic_trend = academic_trend_score(marks)

    # User inputs daily ratings
    daily_ratings = list(map(int, input("Enter your last 7 daily ratings (comma-separated, 1-10): ").split(",")))
    weekly_avg_rating = get_weekly_average(daily_ratings)
    if weekly_avg_rating is None:
        print("⚠️ Not enough daily ratings. You need at least 7.")
        continue

    # User inputs journal entry
    journal_entry = input("Enter your journal entry: ")
    sentiment_probs = get_sentiment_probabilities(journal_entry)

    # Create DataFrame for prediction
    user_data = pd.DataFrame([[
        academic_trend,
        weekly_avg_rating,
        sentiment_probs["negative"],
        sentiment_probs["neutral"],
        sentiment_probs["positive"]
    ]], columns=["academic_trend", "weekly_average_rating", "negative_prob", "neutral_prob", "positive_prob"])

    # Predict mental state
    predicted_score = model.predict(user_data)[0]
    print(f"\n🧠 Predicted Mental State Score: {predicted_score:.4f}")

    # Ask to continue or exit
    choice = input("Would you like to enter another set of data? (yes/no): ").strip().lower()
    if choice != "yes":
        print("👋 Exiting...")
        break

# Final Score Range: -1 to +1
# +0.7 to +1.0 → Excellent Mental State 😊
# High academic trends, good daily ratings, and positive sentiment.
# +0.3 to +0.6 → Good Mental State 🙂
# Balanced lifestyle, moderate daily ratings, and mixed but positive sentiment.
# -0.2 to +0.2 → Neutral Mental State 😐
# Average academic performance, fluctuating daily ratings, and neutral sentiment.
# -0.6 to -0.3 → Poor Mental State 😞
# Low daily ratings, signs of stress or mixed emotions in journal entries.
# -1.0 to -0.7 → Critical Mental State 😔
# Low academic performance, negative journal entries, and low daily ratings.