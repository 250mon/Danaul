import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads') 