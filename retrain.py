# retrain.py - Automatic Feedback Merge + Retraining
import pandas as pd
import re
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from hashlib import md5

print("=== SpamGuardian Pro — Retraining with Feedback ===\n")

MASTER_FILE   = "dataset/master_dataset.csv"
FEEDBACK_FILE = "feedback.csv"
MODEL_PATH    = "model/spam_model.pkl"

# Preprocessor (same as app.py)
def preprocess(text):
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', ' url ', text)
    text = re.sub(r'\S+@\S+', ' email ', text)
    text = re.sub(r'\b\d[\d,\.]+\b', ' number ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

# 1. Load master dataset
if not os.path.exists(MASTER_FILE):
    print("Error: master_dataset.csv not found!")
    exit()

df_master = pd.read_csv(MASTER_FILE)
df_master = df_master.dropna(subset=["text", "label"])
print(f"Master dataset: {len(df_master):,} emails")

# 2. Load feedback
df_feedback = pd.DataFrame()

if os.path.exists(FEEDBACK_FILE) and os.path.getsize(FEEDBACK_FILE) > 10:
    try:
        df_feedback = pd.read_csv(FEEDBACK_FILE)
        # Header duplicate bug fix
        df_feedback = df_feedback[df_feedback["text"] != "text"]
        df_feedback = df_feedback.dropna(subset=["text", "label"])

        if len(df_feedback) > 0:
            print(f"Feedback entries: {len(df_feedback):,}")
            print("Sample feedback:")
            print(df_feedback.head(3))

            # Deduplicate
            df_feedback["hash"] = df_feedback["text"].astype(str).apply(
                lambda x: md5(x.encode()).hexdigest())
            df_feedback = df_feedback.drop_duplicates(subset=["hash"]).drop(columns=["hash"])
            print(f"After dedup: {len(df_feedback):,} unique entries")
        else:
            print("Feedback empty after cleaning.")
            df_feedback = pd.DataFrame()
    except Exception as e:
        print(f"Error reading feedback: {e}")
else:
    print("No feedback found. Training on master only.")

# 3. Merge feedback with boost
if not df_feedback.empty:
    BOOST = 5  # 10x bahut aggressive tha, 5x better hai
    df_boosted = pd.concat([df_feedback] * BOOST, ignore_index=True)
    print(f"Feedback boosted x{BOOST} → {len(df_boosted):,} extra rows")

    df_master = pd.concat([df_master, df_boosted], ignore_index=True)
    df_master = df_master.drop_duplicates(subset=["text"])
    df_master.to_csv(MASTER_FILE, index=False)
    print(f"Master updated: {len(df_master):,} emails total")
else:
    print("No feedback to merge.")

# 4. Sample 100k for fast training (same as train_model.py)
df_master = df_master.dropna(subset=["text", "label"])
if len(df_master) > 100000:
    spam = df_master[df_master["label"] == "spam"].sample(n=50000, random_state=42)
    ham  = df_master[df_master["label"] == "ham"].sample(n=50000, random_state=42)
    df_master = pd.concat([spam, ham]).sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"Using sample: {len(df_master):,} emails (50k spam + 50k ham)")

# 5. Preprocess
df_master["text"] = df_master["text"].apply(preprocess)
df_master = df_master[df_master["text"].str.len() > 5]
print(f"\nFinal training set: {len(df_master):,} emails")

# 6. Train (same config as train_model.py)
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        stop_words='english',
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

print("Training model... (2-3 minutes)")
pipeline.fit(df_master["text"], df_master["label"].map({"spam": 1, "ham": 0}))

os.makedirs("model", exist_ok=True)
joblib.dump(pipeline, MODEL_PATH)

print("\n=== DONE! ===")
print(f"Model saved → {MODEL_PATH}")
print("Restart app: Ctrl+C then python app/app.py")
print("Keep using Wrong Prediction — model aur better hota jayega!")
