import os, requests, smtplib
from dotenv import load_dotenv
from email.message import EmailMessage


# =====================================================
#  Notifier
# =====================================================
class Notifier:
    def __init__(self):
        load_dotenv()
        # Telegram bot TOKEN and channel ID
        self.TOKEN    = os.getenv("TOKEN_MTS")      # bot TOKEN
        self.CHAT_ID  = os.getenv("CHAT_ID_MTS")    # channel ID
        
        # E-mail
        self.EMAIL_FROM  = os.getenv('EMAIL_FROM')
        self.EMAIL_TO    = os.getenv('EMAIL_TO')
        self.EMAIL_PASS  = os.getenv('EMAIL_PASSWORD')
        self.SMTP_SERVER = "smtp.gmail.com"
        self.SMTP_PORT   = 587

    def send_telegram(self, msg):
        payload = {"chat_id": self.CHAT_ID, "text":msg, "parse_mode": "HTML", "disable_web_page_preview": True}
        url = f"https://api.telegram.org/bot{self.TOKEN}/sendMessage"
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        msg_id = r.json()["result"]["message_id"]
        print("Telegram sent.")
        return msg_id
    
    def pin_telegram(self, payload):
        url = f"https://api.telegram.org/bot{self.TOKEN}/pinChatMessage"
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        print("Telegram pinned.")
        
    def send_email(self, subject, body):
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From']    = self.EMAIL_FROM
        msg['To']      = self.EMAIL_TO

        try:
            with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self.EMAIL_FROM, self.EMAIL_PASS)
                server.send_message(msg)
                print("E-mail sent.")
        except Exception as err:
            print(f"E-mail fail: {err}")