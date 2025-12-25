import abc
import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
from typing import List, Dict, Any

class EmailProvider(abc.ABC):
    @abc.abstractmethod
    def connect(self):
        pass

    @abc.abstractmethod
    def fetch_unseen(self) -> List[Dict[str, Any]]:
        pass

    @abc.abstractmethod
    def send_reply(self, to_email: str, subject: str, body: str):
        pass

class IMAPProvider(EmailProvider):
    def __init__(self, imap_server, imap_port, smtp_server, smtp_port, username, password):
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.imap = None

    def connect(self):
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap.login(self.username, self.password)
            print("Connected to IMAP server.")
        except Exception as e:
            print(f"IMAP Connection failed: {e}")

    def fetch_unseen(self) -> List[Dict[str, Any]]:
        if not self.imap:
            self.connect()
            if not self.imap: return []

        emails = []
        try:
            self.imap.select("INBOX")
            status, messages = self.imap.search(None, "UNSEEN")
            email_ids = messages[0].split()

            for eid in email_ids:
                res, msg_data = self.imap.fetch(eid, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        from_ = msg.get("From")
                        
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()

                        emails.append({
                            "id": eid.decode(),
                            "subject": subject,
                            "from": from_,
                            "body": body
                        })
        except Exception as e:
            print(f"Error fetching emails: {e}")
            # Reconnect on next try
            self.imap = None
            
        return emails

    def send_reply(self, to_email: str, subject: str, body: str):
        try:
            msg = MIMEText(body)
            msg["Subject"] = f"Re: {subject}"
            msg["From"] = self.username
            msg["To"] = to_email

            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.username, self.password)
                server.send_message(msg)
                print(f"Sent reply to {to_email}")
        except Exception as e:
            print(f"Error sending email: {e}")

class MockEmailProvider(EmailProvider):
    def connect(self):
        print("Mock Email Provider Connected.")

    def fetch_unseen(self) -> List[Dict[str, Any]]:
        # Return a dummy email occasionally
        import random
        if random.random() > 0.8:
            return [{
                "id": str(random.randint(1000, 9999)),
                "subject": "Help with my order",
                "from": "customer@example.com",
                "body": "I ordered a widget yesterday but haven't received a confirmation."
            }]
        return []

    def send_reply(self, to_email: str, subject: str, body: str):
        print(f"--- MOCK SENDING EMAIL ---")
        print(f"To: {to_email}")
        print(f"Subject: Re: {subject}")
        print(f"Body: {body[:50]}...")
        print("--------------------------")
