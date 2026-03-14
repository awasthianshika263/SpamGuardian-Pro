# 🛡️ SpamGuardian Pro

> AI-Powered Email Spam Detection System with Live Gmail Monitoring

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-black?style=flat-square&logo=flask)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.8-orange?style=flat-square&logo=scikit-learn)
![Status](https://img.shields.io/badge/Status-Live-brightgreen?style=flat-square)

**Live Demo:** [https://spamguardian-pro.onrender.com](https://spamguardian-pro.onrender.com)

---

## 📌 About

SpamGuardian Pro is a machine learning-based web application that detects spam emails in real time. It connects to Gmail via IMAP, monitors incoming emails, and classifies them as **SPAM** or **SAFE** using a trained Logistic Regression model — all processed locally without any third-party API.

---

## ✨ Features

- 🤖 **AI Spam Detection** — Logistic Regression + TF-IDF with 80%+ accuracy
- 📧 **Live Gmail Monitoring** — IMAP polling every 15 seconds
- 📊 **Real-time Dashboard** — Live stats: Scanned, Spam, Safe, Spam Rate
- 🔔 **Instant Alerts** — Live notifications with confidence probability bar
- 🕓 **Email History** — Searchable and filterable table with Export CSV
- 🚩 **Feedback System** — Report wrong predictions to improve the model
- 🌙 **Dark / Light Mode** — Toggle between themes
- 🔒 **100% Local Processing** — No data sent to external servers

---

## 🧠 How It Works

```
Gmail Inbox
    ↓
IMAP Polling (every 15 sec)
    ↓
Text Preprocessing (URLs, HTML, numbers normalized)
    ↓
TF-IDF Vectorization (20,000 features, bigrams)
    ↓
Logistic Regression Classifier
    ↓
SPAM / SAFE  →  Live Dashboard Alert
```

---

## 🗂️ Project Structure

```
EmailSpamWebApp/
├── app/
│   ├── templates/
│   │   └── index.html          # Frontend UI
│   ├── static/
│   │   ├── css/style.css       # Dark/Light theme styles
│   │   └── js/script.js        # Live stream, stats, history
│   └── app.py                  # Flask app + IMAP polling
├── model/
│   └── spam_model.pkl          # Trained ML model
├── scripts/
│   ├── smart_merge.py          # Dataset merging script
│   └── train_model.py          # Model training script
├── retrain.py                  # Retrain with user feedback
├── phrases.json                # Spam phrase boosters
├── requirements.txt
└── .env.example
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask |
| ML Model | Scikit-learn (Logistic Regression) |
| Vectorizer | TF-IDF (20k features, bigrams) |
| Email | IMAP (imaplib) |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5 |
| Deployment | Render |

---

## 📊 Model Details

| Parameter | Value |
|-----------|-------|
| Algorithm | Logistic Regression |
| Training Samples | 100,000 (balanced) |
| Dataset Size | 618,726 emails |
| TF-IDF Features | 20,000 |
| N-gram Range | (1, 2) |
| Spam Threshold | 0.45 |
| Accuracy | 80%+ |

---

## 🚀 Local Setup

### Prerequisites
- Python 3.10+
- Gmail account with 2FA enabled
- Gmail App Password

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/awasthianshika263/SpamGuardian-Pro.git
cd SpamGuardian-Pro

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment variables
cp .env.example .env
# Edit .env with your Gmail credentials

# 5. Run the app
python app/app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## 🔐 Environment Variables

Create a `.env` file:

```env
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
POLL_INTERVAL=15
```

> **Note:** Use Gmail App Password (not your regular password). Enable 2FA first, then generate App Password from [Google Account Settings](https://myaccount.google.com/apppasswords).

---

## 🔄 Retrain Model with Feedback

Users can report wrong predictions via **"Wrong? Report it"** button. To retrain:

```bash
python retrain.py
```

---

## 🌐 Deployment

Deployed on **Render** (Free tier).

> ⚠️ Free instances spin down after inactivity — first load may take 50+ seconds.

---

## 🔮 Future Scope

- 🔐 Multi-user support with OAuth2 login
- 📱 Mobile responsive UI
- 📈 Advanced model (BERT / Deep Learning)
- 🗃️ Database integration (PostgreSQL)
- 📬 Support for Outlook, Yahoo Mail

---

## 👩‍💻 Developer

**Anshika Awasthi**
- GitHub: [@awasthianshika263](https://github.com/awasthianshika263)

---

<p align="center">Made with ❤️ for MCA Project</p>
