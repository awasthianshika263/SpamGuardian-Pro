# app.py — SpamGuardian Pro (Enhanced)
import os, re, time, imaplib, email, json, threading
import pandas as pd
from collections import deque
from email import policy
from email.utils import parseaddr
from flask import Flask, render_template, jsonify, Response, request
from dotenv import load_dotenv
import joblib
from bs4 import BeautifulSoup

load_dotenv()

IMAP_HOST           = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_USER          = os.getenv("EMAIL_USER")
EMAIL_PASS          = os.getenv("EMAIL_PASS")
POLL_INTERVAL       = int(os.getenv("POLL_INTERVAL", "15"))
SPAM_PROB_THRESHOLD = 0.45  # Sensitive threshold

app = Flask(__name__)
notifications = deque(maxlen=100)
stats = {"total": 0, "spam": 0, "safe": 0}

PROCESSED_FILE = "processed_uids.txt"

def load_processed_uids():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return {line.strip() for line in f if line.strip()}
    return set()

def save_processed_uid(uid):
    with open(PROCESSED_FILE, "a") as f:
        f.write(f"{uid}\n")

# LOAD MODEL
MODEL_PATH = os.path.join("model", "spam_model.pkl")
try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Model loading failed: {e}")
    exit(1)

# LOAD PHRASES
spam_phrases = []
try:
    phrases_path = "phrases.json"
    with open(phrases_path) as f:
        phrases = json.load(f)
    spam_phrases = [p.lower() for p in phrases.get("spam", [])
                    if not p.strip().startswith("#")]
    print(f"Loaded {len(spam_phrases)} spam phrases.")
except Exception as e:
    print(f"phrases.json not loaded: {e}")

def phrase_boost(text):
    text_lower = text.lower()
    for phrase in spam_phrases:
        if phrase in text_lower:
            return 0.20
    return 0.0

# TEXT PREPROCESSOR
def preprocess(text):
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', ' url ', text)
    text = re.sub(r'\S+@\S+', ' email ', text)
    text = re.sub(r'\b\d[\d,\.]+\b', ' number ', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def classify(text):
    processed = preprocess(text)
    try:
        prob = model.predict_proba([processed])[0][1]
        prob = min(1.0, prob + phrase_boost(text))
        label = "SPAM" if prob >= SPAM_PROB_THRESHOLD else "SAFE"
        return label, round(prob, 3)
    except Exception:
        return "SAFE", 0.0

# EMAIL BODY EXTRACTION
def get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get('Content-Disposition') == "attachment":
                continue
            ctype = part.get_content_type()
            payload = part.get_payload(decode=True)
            if payload:
                if ctype == "text/plain":
                    body += payload.decode(errors="ignore") + " "
                elif ctype == "text/html":
                    soup = BeautifulSoup(payload.decode(errors="ignore"), "html.parser")
                    body += soup.get_text(separator=" ", strip=True) + " "
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            if msg.get_content_type() == "text/html":
                soup = BeautifulSoup(payload.decode(errors="ignore"), "html.parser")
                body = soup.get_text(separator=" ", strip=True)
            else:
                body = payload.decode(errors="ignore")
    return body.strip()

def fetch_message_by_uid(mail, uid):
    typ, data = mail.uid("fetch", uid, "(BODY.PEEK[])")
    if typ != "OK" or not data[0]:
        return None
    raw = data[0][1] if isinstance(data[0], tuple) else data[0]
    return email.message_from_bytes(raw, policy=policy.default)

def poll_inbox():
    if not EMAIL_USER or not EMAIL_PASS:
        return
    print(f"Polling inbox... [{time.strftime('%H:%M:%S')}]")
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select('INBOX')
        status, data = mail.uid("search", None, "UNSEEN")
        if status != "OK" or not data[0]:
            mail.logout(); return
        uids = data[0].split()
        if not uids:
            mail.logout(); return
        processed_uids = load_processed_uids()
        new_uids = [uid.decode() for uid in uids if uid.decode() not in processed_uids]
        if not new_uids:
            mail.logout(); return
        for uid in new_uids:
            msg = fetch_message_by_uid(mail, uid)
            if not msg: continue
            subject  = msg.get("subject", "(no subject)")
            sender   = parseaddr(msg.get("from", ""))[1] or "Unknown"
            body     = get_body(msg)
            full_text = f"{subject} {body}".strip()
            if len(full_text) < 10: continue
            label, prob = classify(full_text)
            stats["total"] += 1
            stats["spam" if label == "SPAM" else "safe"] += 1
            notifications.appendleft({
                "time": time.strftime("%H:%M:%S"),
                "from": sender, "subject": subject,
                "text": full_text[:300] + ("..." if len(full_text) > 300 else ""),
                "label": label, "prob": prob
            })
            save_processed_uid(uid)
        mail.logout()
    except Exception as e:
        print(f"IMAP ERROR: {e}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"label": "SAFE", "prob": 0.0})
    label, prob = classify(text)
    return jsonify({"label": label, "prob": prob})

@app.route("/feedback", methods=["POST"])
def feedback():
    data       = request.get_json()
    text       = data.get("text", "").strip()
    true_label = data.get("label", "ham")
    if not text:
        return jsonify({"status": "error"})
    feedback_file = "feedback.csv"
    file_exists   = os.path.exists(feedback_file) and os.path.getsize(feedback_file) > 5
    df = pd.DataFrame([[text, true_label]], columns=["text", "label"])
    df.to_csv(feedback_file, mode='a', header=not file_exists, index=False)
    return jsonify({"status": "saved"})

@app.route("/stats")
def get_stats():
    return jsonify(stats)

@app.route("/stream")
def stream():
    def event_stream():
        for notif in reversed(list(notifications)):
            yield f"data: {json.dumps(notif)}\n\n"
            time.sleep(0.05)
        last_sent = len(notifications)
        while True:
            current = len(notifications)
            if current > last_sent:
                new_ones = list(notifications)[0:current - last_sent]
                for notif in reversed(new_ones):
                    yield f"data: {json.dumps(notif)}\n\n"
                last_sent = current
            time.sleep(0.5)
    return Response(event_stream(), mimetype="text/event-stream")

def background_job():
    while True:
        poll_inbox()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    print("SpamGuardian Pro → http://127.0.0.1:5000")
    t = threading.Thread(target=background_job, daemon=True)
    t.start()
    # app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)), debug=False, use_reloader=False)