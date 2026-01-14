from flask import Flask, render_template, request
import requests, json, time, threading, schedule
from datetime import datetime
import os, smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# =========================
# 🔧 LOAD ENV
# =========================
load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

if not RAPIDAPI_KEY:
    raise RuntimeError("❌ RAPIDAPI_KEY not set in environment variables")

# =========================
# 🌐 FLASK APP
# =========================
app = Flask(__name__)

RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
DATA_FILE = "jobs_data.json"

# =========================
# 📂 FILE HELPERS
# =========================
def load_seen_jobs():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_seen_jobs(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# 🔍 FETCH JOBS
# =========================
def fetch_jobs(job_title, location):
    url = "https://jsearch.p.rapidapi.com/search"

    params = {
        "query": f"{job_title} in {location}",
        "page": "1",
        "num_pages": "1"
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        data = response.json()

        if "data" not in data:
            return []

        jobs = []
        for job in data["data"]:
            jobs.append({
                "job_id": job.get("job_id", ""),
                "title": job.get("job_title", "No Title"),
                "company_name": job.get("employer_name", "Unknown"),
                "location": f"{job.get('job_city', '')}, {job.get('job_country', '')}",
                "link": job.get("job_apply_link", "#")
            })

        return jobs

    except Exception as e:
        print("❌ Job fetch error:", e)
        return []

# =========================
# ✉️ EMAIL ALERT
# =========================
def send_email_alert(subject, html_body, plain_body):
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        print("⚠️ Email credentials missing")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECIPIENT
        msg["Subject"] = subject

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print("✉️ Email sent")

    except Exception as e:
        print("❌ Email error:", e)

# =========================
# 🚨 JOB CHECKER
# =========================
def check_new_jobs():
    searches = [
        {"job_title": "Data Analyst", "location": "Pune"},
        {"job_title": "Data Scientist", "location": "India"}
    ]

    seen = load_seen_jobs()

    for s in searches:
        jobs = fetch_jobs(s["job_title"], s["location"])
        seen.setdefault(s["job_title"], [])

        new_jobs = [j for j in jobs if j["job_id"] not in seen[s["job_title"]]]

        if new_jobs:
            html = "<ul>"
            text = ""
            for j in new_jobs:
                html += f"<li><b>{j['title']}</b> — {j['company_name']}<br><a href='{j['link']}'>Apply</a></li>"
                text += f"{j['title']} — {j['company_name']}\n{j['link']}\n\n"
                seen[s["job_title"]].append(j["job_id"])
            html += "</ul>"

            send_email_alert(
                f"🚀 New {s['job_title']} Jobs",
                html,
                text
            )

    save_seen_jobs(seen)

# =========================
# ⏰ SCHEDULER (SAFE)
# =========================
def start_scheduler():
    schedule.every().day.at("09:00").do(check_new_jobs)
    while True:
        schedule.run_pending()
        time.sleep(60)

# =========================
# 🌐 ROUTES
# =========================
@app.route("/", methods=["GET", "POST"])
def home():
    jobs = []
    job_title = ""
    location = ""

    if request.method == "POST":
        job_title = request.form.get("job_title")
        location = request.form.get("location")
        jobs = fetch_jobs(job_title, location)

    return render_template(
        "index.html",
        jobs=jobs,
        job_title=job_title,
        location=location
    )

# =========================
# ▶️ START APP
# =========================
if __name__ == "__main__":
    print("🚀 Job Alert Web App Started")

    # Start scheduler in background thread (LOCAL USE)
    threading.Thread(target=start_scheduler, daemon=True).start()

    app.run()
