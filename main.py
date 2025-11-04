import imaplib
import email
from email.header import decode_header
import os
from pathlib import Path
from dotenv import load_dotenv
import datetime
import smtplib
from email.mime.text import MIMEText

def log_message(message):
    # Write a timestamped message to the log file
    log_file = os.getenv("LOG_FILE", "logs/organizer.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)

    print(line.strip())  # Also show it in console


# Load environment variables
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', 'downloads'))
DAYS_LOOKBACK = int(os.getenv('DAYS_LOOKBACK', 1))

# Ensure download folders exist
for sub in ["invoices", "reports", "images", "misc"]:
    (DOWNLOAD_DIR / sub).mkdir(parents=True, exist_ok=True)


def categorize_file(filename):
    # Categorize file based on extension
    fn = filename.lower()
    if fn.endswith(('.pdf', '.docx', '.doc', '.xls', '.xlsx')):
        return "invoices"
    elif fn.endswith(('.csv', '.txt')):
        return "reports"
    elif fn.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        return "images"
    else:
        return "misc"


def fetch_attachments():
    # Fetch recent emails and save attachments locally
    print("Connecting to Gmail...")
    log_message("Connecting to Gmail...")
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL_USER, EMAIL_PASSWORD)
    mail.select("inbox")

    # Search for emails since X days ago
    since_date = (datetime.date.today() - datetime.timedelta(DAYS_LOOKBACK)).strftime("%d-%b-%Y")
    status, data = mail.search(None, f'(SINCE "{since_date}")')

    if status != "OK":
        print("No messages found.")
        return

    email_ids = data[0].split()
    print(f"Found {len(email_ids)} emails since {since_date}.")
    log_message(f"Found {len(email_ids)} emails since {since_date}.")

    saved_files = []

    for num in email_ids:
        status, msg_data = mail.fetch(num, "(RFC822)")
        if status != "OK":
            continue

        msg = email.message_from_bytes(msg_data[0][1])

        subject, encoding = decode_header(msg.get("Subject", ""))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="ignore")

        from_ = msg.get("From", "Unknown Sender")

        # Iterate over message parts
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = part.get_content_disposition()
                if content_disposition == "attachment":
                    filename = part.get_filename()
                    if not filename:
                        continue

                    decoded = decode_header(filename)[0]
                    if isinstance(decoded[0], bytes):
                        filename = decoded[0].decode(decoded[1] or "utf-8", errors="ignore")

                    folder = categorize_file(filename)
                    save_path = DOWNLOAD_DIR / folder / filename

                    with open(save_path, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    saved_files.append((filename, folder, from_))
                    print(f"Saved: {filename} → {folder}/")

    mail.logout()

    if saved_files:
        print("\nDownload complete! Files saved:")
        for f, folder, sender in saved_files:
            print(f"   - {f} from {sender} → {folder}/")
    else:
        print("\nNo attachments found in recent emails.")

    # Build summary text
    if saved_files:
        lines = [f"Processed {len(saved_files)} attachments:\n"]
        for f, folder, sender in saved_files:
            lines.append(f"- {f} from {sender} → {folder}/")
        summary_body = "\n".join(lines)
    else:
        summary_body = "No attachments found in recent emails."

    send_summary_email("Daily Attachment Summary", summary_body)
    log_message("Summary email sent successfully.")

def send_summary_email(subject, body):
    #Send a simple summary email using SMTP
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    summary_to = os.getenv('SUMMARY_TO', smtp_user)

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = summary_to

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print("Summary email sent.")
    except Exception as e:
        print("Failed to send summary email:", e)



if __name__ == "__main__":
    fetch_attachments()
