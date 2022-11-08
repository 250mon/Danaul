import email, smtplib, ssl
import os
import glob

import utils
from utils import config_reader

from email import encoders
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(self):
        # Read from config file
        self.options = self.read_config()

        # Options from config file
        self.year_month = self.options['year_month']
        self.year = self.year_month[0:2]
        self.month = self.year_month[2:4].lstrip('0')
        self.subject = self.year + '년 ' + self.month + self.options['subject']
        self.body = self.options['body']
        self.dir_path = self.options['dir_path'] + '\\' + self.year_month
        self.filename_prefix = self.options['filename_beg'] + self.month + self.options['filename_end']

        # self.smtp_server = "smtp.gmail.com"
        # self.port = 587  # For starttls
        self.smtp_server = self.options['smtp_server']
        self.port = int(self.options['port'])
        self.sender_email = self.options['sender_email']
        # self.password = self.options['password']
        self.password = input("Type your password and press enter: ")

    def read_config(self):
        # Read options from config file
        options = config_reader("config")
        return options

    def create_message(self, receiver_email):
        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = receiver_email
        message["Subject"] = self.subject
        message["Bcc"] = receiver_email  # Recommended for mass emails

        # Add body to email
        message.attach(MIMEText(self.body, "plain"))
        return message

    def create_attachment(self, file_name):
        file_path = os.path.join(self.dir_path, file_name)
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
        return part

    def send_email(self, receiver_email, attached_file):
        message = self.create_message(receiver_email)
        part = self.create_attachment(attached_file)

        # Add attachment to message and convert message to string
        message.attach(part)
        text = message.as_string()

        # Create a secure SSL context
        context = ssl.create_default_context()

        # Try to log in to server and send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.port)
            server.ehlo() # can be omitted
            server.starttls(context=context) # Secure the connection
            server.ehlo() # can be omitted
            server.login(self.sender_email, self.password)
            # Send email
            server.sendmail(self.sender_email, receiver_email, text)
            # server.send_message(message)
        except Exception as e:
            # Print any error messages to stdout
            print(e)
        finally:
            server.quit()

    def read_addressbook(self):
        addrs = utils.config_reader('address')
        files_to_attach = map(self.find_file_by_name, addrs.keys())
        # print(list(files_to_attach))
        list(map(self.send_email, addrs.values(), files_to_attach))

        # for name in addrs.keys():
        #     file_to_attach = self.find_file_by_name(name)
        #     print(file_to_attach)
        #     # file_to_attach = self.filename_prefix + name + '.pdf'
        #     addr = addrs[name]
        #     self.send_email(addr, file_to_attach)

    def find_file_by_name(self, name):
        files = glob.glob(os.path.join(self.dir_path, f'*{name}*'))
        if files:
            return os.path.basename(files[0])
        else:
            return None


if __name__ == "__main__":
    esender = EmailSender()
    esender.read_addressbook()
