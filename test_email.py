import os, smtplib, ssl
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # load .env values

print("RAPIDAPI_KEY loaded:", bool(os.getenv("RAPIDAPI_KEY")))
print("EMAIL_SENDER:", os.getenv("EMAIL_SENDER"))


EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

print("🔍 Checking environment variables...")
print("Sender:", EMAIL_SENDER)
print("Recipient:", EMAIL_RECIPIENT)

if not EMAIL_SENDER or not EMAIL_PASSWORD:
    print("❌ Missing email credentials in .env")
    exit()

try:
    msg = MIMEText("✅ This is a test email from your Flask Job Alert App.")
    msg["Subject"] = "Job Alert Test Email"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

    print("✉️ Test email sent successfully! Check your inbox.")
except Exception as e:
    print("❌ Failed to send test email:", e)
