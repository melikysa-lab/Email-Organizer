Email Organizer Pro

This script automatically downloads and organizes email attachments from Gmail.
You’ll receive a daily summary email of all files saved.

SETUP INSTRUCTIONS

1. Install Python 3.10 or higher:
   https://www.python.org/downloads/

2. Open Command Prompt or PowerShell in this folder and run:
   pip install -r requirements.txt

3. Create a new file called ".env"
   Copy everything from ".env.example" into it and fill out your info:
     - Gmail address
     - Gmail App Password
     - Destination email for daily summaries

4. Allow "App Passwords" in your Google Account
   (My Account → Security → App Passwords → Generate 16-char key)

5. Run the script manually to test:
   python main.py

6. (Optional) Schedule it to run daily using Task Scheduler.

Your attachments will appear in the /downloads/ folder.
Logs are stored in /logs/organizer.log.
