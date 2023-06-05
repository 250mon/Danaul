import smtplib, ssl
import os
import glob
import utils
from utils import config_reader
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    def __init__(self):
        # Read from config file
        self.options = self.read_config()

        # create contents of email to send
        self.subject = None
        self.body = None
        self.dir_path = None
        self.create_contents()

        # SMTP setting
        # self.smtp_server = "smtp.gmail.com"
        # self.port = 587  # For starttls
        self.smtp_server = self.options['smtp_server']
        self.port = int(self.options['port'])
        self.sender_email = self.options['sender_email']
        pw = self.options['password']
        self.password = pw if pw else input("Type your password and press enter: ")

        self.ans = False

    def create_contents(self):
        '''
        make subject, body text and dir_path of the files to be attached
        :return:
        '''
        # extract year and month info for salary slip
        year_month = self.options['year_month']
        year = year_month[0:2]
        month = year_month[2:4].lstrip('0')
        # make email subject, body, dir_path containing the files to be attached
        self.subject = year + '년 ' + month + self.options['subject']
        self.body = self.options['body']
        self.dir_path = self.options['dir_path']

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

    def create_attachment(self, file_path):
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
        file_name = os.path.basename(file_path)
        part.add_header("Content-Disposition", 'attachment', filename=str(file_name))
        return part

    def send_email(self, addr_files):
        receiver_email, attached_files = addr_files
        message = self.create_message(receiver_email)
        if len(attached_files) == 0:
            print(f'No file found to send for {receiver_email}.')
            return

        # attach files to message
        for file in attached_files:
            print(f'sending {file} ...')
            part = self.create_attachment(file)
            # Add attachment to message
            message.attach(part)

        # convert message to string
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

    def find_files_by_name(self, name):
        # searching the directory including subdirectories
        dir_name = self.dir_path + "\**"
        files = glob.glob(os.path.join(dir_name, f'*{name}*.pdf'), recursive=True)
        print(f'\nfiles are {files}')
        files_to_send = []
        for file in files:
            ans = input(f'{file}: are you sure to send? (a(all) / y(yes) / n(no)) ')
            if not self.ans and ans.lower() == 'a':
                self.ans = True
            if self.ans or ans.lower() == 'y':
                files_to_send.append(file)
        return files_to_send

    def main(self):
        addrs = utils.config_reader('address.sh')
        # find the exact file path to attach
        files_to_attach = map(self.find_files_by_name, addrs.keys())
        addr_files_pair = zip(addrs.values(), files_to_attach)
        list(map(self.send_email, addr_files_pair))


if __name__ == "__main__":
    esender = EmailSender()
    esender.main()
