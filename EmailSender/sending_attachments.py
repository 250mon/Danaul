import email, smtplib, ssl
import os
from util import config_reader

from email import encoders
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Read options from config file
options = config_reader()

# Options from config file
subject = options['subject']
body = options['body']
dir_path = options['dir_path']
file_name = options['file_name']
file_path = os.path.join(dir_path, file_name)


smtp_server = "smtp.gmail.com"
port = 587  # For starttls
sender_email = "danaulns@gmail.com"
receiver_email = "danaulns@naver.com"
password = input("Type your password and press enter: ")

# subject = "An email with attachment from Python"
# body = "This is an email with attachment sent from Python"

# Create a multipart message and set headers
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message["Bcc"] = receiver_email  # Recommended for mass emails

# Add body to email
message.attach(MIMEText(body, "plain"))

# Open PDF file in binary mode
with open(file_path, "rb") as attachment:
    # Add file as application/octet-stream
    # Email client can usually download this automatically as attachment
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())
    # part = MIMEApplication(attachment.read(), _subtype="pdf")

# Encode file in ASCII characters to attachment part
encoders.encode_base64(part)

# Add header as key/value pair to attachment part
part.add_header("Content-Disposition", 'attachment', filename=str(file_name))

# Add attachment to message and convert message to string
message.attach(part)
text = message.as_string()

# Create a secure SSL context
context = ssl.create_default_context()

# Try to log in to server and send email
try:
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo() # can be omitted
    server.starttls(context=context) # Secure the connection
    server.ehlo() # can be omitted
    server.login(sender_email, password)
    # Send email
    server.sendmail(sender_email, receiver_email, text)
    # server.send_message(message)
except Exception as e:
    # Print any error messages to stdout
    print(e)
finally:
    server.quit()
