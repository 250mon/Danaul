import smtplib
import ssl
import os
import glob
import re
import fnmatch
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Tuple

from utils import config_reader

class EmailSender:
    def __init__(self):
        self.options = self.read_config()
        self.subject, self.body, self.dir_path = self.create_contents()
        self.smtp_server = self.options['smtp_server']
        self.port = int(self.options['port'])
        self.sender_email = self.options['sender_email']
        self.password = self.options['password'] or input("Type your password and press enter: ")
        self.send_all = False

    @staticmethod
    def read_config() -> Dict[str, str]:
        return config_reader("config")

    def create_contents(self) -> Tuple[str, str, str]:
        if self.options['other_purpose'] != 'yes':
            year, month = self.options['year_month'][:2], self.options['year_month'][2:4].lstrip('0')
            subject = f"{year}년 {month}{self.options['subject']}"
            body = self.options['body']
            dir_path = self.options['dir_path']
        else:
            subject = self.options['subject_2']
            body = self.options['body_2']
            dir_path = self.options['dir_path_2']

        print(f"Title: {subject}")
        return subject, body, dir_path

    def create_message(self, receiver_email: str) -> MIMEMultipart:
        message = MIMEMultipart()
        message["From"] = self.sender_email
        message["To"] = receiver_email
        message["Subject"] = self.subject
        message.attach(MIMEText(self.body, "plain"))
        return message

    @staticmethod
    def create_attachment(file_path: str) -> MIMEBase:
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        file_name = os.path.basename(file_path)
        part.add_header("Content-Disposition", 'attachment', filename=str(file_name))
        return part

    def send_email(self, addr_files: Tuple[Tuple[str, str], List[str]]):
        receiver, attached_files = addr_files
        if not attached_files:
            print(f'No file found to send for {receiver}.')
            return

        print(f'Receiver: {receiver}.')
        message = self.create_message(receiver[1])

        for file in attached_files:
            print(f'sending {file} ...')
            part = self.create_attachment(file)
            message.attach(part)

        text = message.as_string()
        context = ssl.create_default_context()

        try:
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, receiver[1], text)
        except Exception as e:
            print(f"Error sending email to {receiver[1]}: {e}")

    def find_files_by_name(self, name: str) -> List[str]:
        file_pattern = re.compile(fnmatch.translate(f'*{name}*.pdf'), re.IGNORECASE)
        all_files = glob.glob(f'{self.dir_path}/**', recursive=True)
        files = [file for file in all_files if file_pattern.search(file)]
        
        print(f'\nFiles found: {files}')
        files_to_send = []
        for file in files:
            if self.send_all or input(f'{file}: are you sure to send to {name}? (a(all) / y(yes) / n(no)) ').lower() in ['a', 'y']:
                files_to_send.append(file)
            if not self.send_all and input('Send all remaining files? (y/n) ').lower() == 'y':
                self.send_all = True
                files_to_send.extend(files[files.index(file)+1:])
                break
        return files_to_send

    def main(self):
        addrs = config_reader('address.sh')
        files_to_attach = map(self.find_files_by_name, addrs.keys())
        addr_files_pair = zip(addrs.items(), files_to_attach)
        list(map(self.send_email, addr_files_pair))

if __name__ == "__main__":
    EmailSender().main()
