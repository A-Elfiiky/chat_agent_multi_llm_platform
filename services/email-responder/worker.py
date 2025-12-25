import time
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))
from email_adapter import MockEmailProvider, IMAPProvider

# Add parent directory to path to import shared modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from services.shared.config_utils import load_config

class EmailResponder:
    def __init__(self):
        self.config = load_config()
        self.check_interval = self.config['email']['check_interval_seconds']
        self.provider_type = self.config['email']['provider']
        
        if self.provider_type == 'imap':
            # In a real app, these would come from config/env
            self.provider = IMAPProvider(
                imap_server=os.getenv("IMAP_SERVER", "imap.gmail.com"),
                imap_port=993,
                smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                smtp_port=465,
                username=os.getenv("EMAIL_USER", "user@example.com"),
                password=os.getenv("EMAIL_PASS", "password")
            )
        else:
            self.provider = MockEmailProvider()
            
        self.provider.connect()
        print(f"Email Responder initialized. Provider: {self.provider_type}")

    def fetch_emails(self):
        return self.provider.fetch_unseen()

    def process_email(self, email):
        print(f"Processing email: {email['subject']}")
        
        # 1. Construct Query from Subject + Body
        query = f"{email['subject']}\n{email['body']}"
        
        # 2. Call Chat Service via Gateway or Direct
        # In a real deployment, we might use the internal service URL
        chat_url = "http://localhost:8002/chat" 
        
        try:
            import requests
            response = requests.post(chat_url, json={"message": query})
            if response.status_code == 200:
                data = response.json()
                draft_response = data['answer_text']
                confidence = data['confidence']
                citations = data['citations']
                
                # 3. Create Draft / Send Reply
                # For now, we'll just "send" it if confidence is high, or log it
                if confidence > 0.8:
                    self.provider.send_reply(email['from'], email['subject'], draft_response)
                else:
                    print(f"Low confidence ({confidence}). Draft saved for review.")
                    # In real app: save to DB 'tickets' table
            else:
                print(f"Failed to get AI response: {response.status_code}")
                
        except Exception as e:
            print(f"Error calling chat service: {e}")

    def run(self):
        print("Starting Email Responder Loop...")
        while True:
            try:
                emails = self.fetch_emails()
                for email in emails:
                    self.process_email(email)
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                print("Stopping Email Responder...")
                break
            except Exception as e:
                print(f"Error in email loop: {e}")
                time.sleep(10)

if __name__ == "__main__":
    responder = EmailResponder()
    responder.run()

