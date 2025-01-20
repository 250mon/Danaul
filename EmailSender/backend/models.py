from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
        }

class EmailHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    files = db.Column(db.Text, nullable=False)  # Store as JSON string
    status = db.Column(db.String(20), nullable=False)  # 'success', 'error', 'skipped'
    message = db.Column(db.Text)  # For error messages or additional info
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now())

    def to_dict(self):
        return {
            'id': str(self.id),
            'recipient_name': self.recipient_name,
            'recipient_email': self.recipient_email,
            'subject': self.subject,
            'files': self.files,  # Frontend will need to parse this JSON string
            'status': self.status,
            'message': self.message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        } 