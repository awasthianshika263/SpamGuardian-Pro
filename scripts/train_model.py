# scripts/train_model.py
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

# Paths
DATASET_PATH = os.path.join("dataset", "master_dataset.csv")
MODEL_PATH = os.path.join("model", "spam_model.pkl")

print("Training model on master_dataset.csv...")

# Load master dataset
df = pd.read_csv(DATASET_PATH)
df = df.dropna(subset=["text", "label"])
print(f"Loaded {len(df):,} emails | Spam: {len(df[df['label']=='spam']):,} | Ham: {len(df[df['label']=='ham']):,}")

# 100k balanced sample lo — fast + accurate
if len(df) > 100000:
    spam = df[df["label"] == "spam"].sample(n=50000, random_state=42)
    ham  = df[df["label"] == "ham"].sample(n=50000, random_state=42)
    df   = pd.concat([spam, ham]).sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"Using balanced sample: {len(df):,} emails (50k spam + 50k ham)")

# Build pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=20000,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True
    )),
    ('clf', LogisticRegression(
        C=5.0,
        max_iter=1000,
        class_weight='balanced',
        solver='lbfgs',
        n_jobs=-1
    ))
])

# Train
print("Training model... (2-3 minutes)")
pipeline.fit(df["text"], df["label"].map({"spam": 1, "ham": 0}))

# Save model
os.makedirs("model", exist_ok=True)
joblib.dump(pipeline, MODEL_PATH)
print(f"Model saved → {MODEL_PATH}")
print("TRAINING COMPLETE! Now run app.py")

