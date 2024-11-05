import smtplib
import ssl
import os
import urllib.parse
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from typing import List, Dict

class EmailSender:
    def __init__(self, smtp_config: Dict):
        self.smtp_server = smtp_config['smtp_server']
        self.port = smtp_config['port']
        self.sender_email = smtp_config['sender_email']
        self.password = smtp_config['password']

    def create_message(self, receiver_email: str, subject: str, body: str) -> MIMEMultipart:
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        return message

    def attach_files(self, message: MIMEMultipart, files: List[str]) -> None:
        for file_path in files:
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                
                # Get original filename and decode if it's URL encoded
                filename = os.path.basename(file_path)
                if '%' in filename:
                    filename = urllib.parse.unquote(filename)

                # RFC 2231 encoding for filename
                filename_encoded = filename.encode('utf-8')
                filename_str = filename_encoded.decode('latin-1')
                
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=('utf-8', '', filename)  # This is the key change
                )
                message.attach(part)

    def send_email(self, receiver_email: str, subject: str, body: str, files: List[str]) -> Dict:
        try:
            message = self.create_message(receiver_email, subject, body)
            if files:
                self.attach_files(message, files)

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, receiver_email, message.as_string())
            
            return {"success": True, "message": f"Email sent successfully to {receiver_email}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send email to {receiver_email}: {str(e)}"} 