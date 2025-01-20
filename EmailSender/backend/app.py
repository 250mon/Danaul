import urllib.parse
from pathlib import Path
import json
from datetime import datetime
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import Config
from email_sender import EmailSender
from models import Address, db, EmailHistory

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
app.config.from_object(Config)

# Initialize SQLAlchemy
db.init_app(app)

# Ensure upload folder exists
UPLOAD_FOLDER = Path(app.config["UPLOAD_FOLDER"])
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Ensure data directory exists
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Create database tables
with app.app_context():
    db.create_all()


def secure_filename_with_hangul(filename):
    """Custom secure filename function that preserves Korean characters"""
    filename_encoded = urllib.parse.quote(filename)
    filename_safe = "".join(
        c for c in filename_encoded if c.isalnum() or c in ["%", "-", "_", "."]
    )
    return filename_safe


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "files" not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist("files")
    uploaded_files = []

    for file in files:
        if file.filename:
            try:
                filename = secure_filename_with_hangul(file.filename)
                filepath = UPLOAD_FOLDER / filename

                # Ensure unique filename
                counter = 0
                while filepath.exists():
                    counter += 1
                    name_parts = filename.rsplit(".", 1)
                    if len(name_parts) > 1:
                        filepath = (
                            UPLOAD_FOLDER / f"{name_parts[0]}_{counter}.{name_parts[1]}"
                        )
                    else:
                        filepath = UPLOAD_FOLDER / f"{filename}_{counter}"

                file.save(filepath)

                # For display purposes, decode the filename
                display_name = urllib.parse.unquote(filepath.name)
                uploaded_files.append({"path": str(filepath), "name": display_name})
            except Exception as e:
                return (
                    jsonify({"error": f"Error saving file {file.filename}: {str(e)}"}),
                    500,
                )

    return jsonify({"message": "Files uploaded successfully", "files": uploaded_files})


@app.route("/api/send-email", methods=["POST"])
def send_email():
    data = request.json
    files_to_send = [f["path"] for f in data.get("files", [])]

    smtp_config = {
        "smtp_server": app.config["SMTP_SERVER"],
        "port": app.config["SMTP_PORT"],
        "sender_email": app.config["SENDER_EMAIL"],
        "password": app.config["SMTP_PASSWORD"],
    }

    email_sender = EmailSender(smtp_config)
    result = email_sender.send_email(
        receiver_email=data["receiver_email"],
        subject=data["subject"],
        body=data["body"],
        files=files_to_send,
    )

    # Save to email history
    history = EmailHistory(
        recipient_name=data.get("recipient_name", ""),
        recipient_email=data["receiver_email"],
        subject=data["subject"],
        files=json.dumps([f["name"] for f in data.get("files", [])]),
        status='success' if result['success'] else 'error',
        message=result['message']
    )
    
    try:
        db.session.add(history)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Failed to save email history: {str(e)}")

    # Clean up uploaded files after sending
    for file_path in files_to_send:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            app.logger.error(f"Failed to delete file {file_path}: {str(e)}")

    return jsonify(result)


@app.route("/api/email-history", methods=["GET"])
def get_email_history():
    try:
        # Optional query parameters for filtering
        recipient = request.args.get('recipient')
        subject = request.args.get('subject')
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        query = EmailHistory.query

        if recipient:
            query = query.filter(
                db.or_(
                    EmailHistory.recipient_name.ilike(f'%{recipient}%'),
                    EmailHistory.recipient_email.ilike(f'%{recipient}%')
                )
            )
        
        if subject:
            query = query.filter(EmailHistory.subject.ilike(f'%{subject}%'))
        
        if status:
            query = query.filter(EmailHistory.status == status)

        if date_from:
            date_from = datetime.fromisoformat(date_from)
            query = query.filter(EmailHistory.sent_at >= date_from)

        if date_to:
            date_to = datetime.fromisoformat(date_to)
            query = query.filter(EmailHistory.sent_at <= date_to)

        # Order by most recent first
        history = query.order_by(EmailHistory.sent_at.desc()).all()
        return jsonify([h.to_dict() for h in history])

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/addresses", methods=["GET", "POST", "PUT", "DELETE"])
def manage_addresses():
    try:
        if request.method == "GET":
            addresses = Address.query.all()
            return jsonify([address.to_dict() for address in addresses])

        elif request.method == "POST":
            data = request.json
            new_address = Address(
                name=data["name"],
                email=data["email"],
            )
            db.session.add(new_address)
            db.session.commit()
            return jsonify(new_address.to_dict())

        elif request.method == "PUT":
            data = request.json
            address = Address.query.get(int(data["id"]))
            if not address:
                return jsonify({"error": "Address not found"}), 404

            address.name = data["name"]
            address.email = data["email"]
            db.session.commit()
            return jsonify(address.to_dict())

        elif request.method == "DELETE":
            address_id = request.args.get("id")
            address = Address.query.get(int(address_id))
            if not address:
                return jsonify({"error": "Address not found"}), 404

            db.session.delete(address)
            db.session.commit()
            return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

