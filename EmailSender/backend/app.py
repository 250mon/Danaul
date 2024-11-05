import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path
import urllib.parse
from config import Config
from email_sender import EmailSender
import json

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

# Ensure upload folder exists
UPLOAD_FOLDER = Path(app.config['UPLOAD_FOLDER'])
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Add these paths after app configuration
DATA_DIR = Path(__file__).parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
ADDRESS_FILE = DATA_DIR / 'addresses.json'

# Initialize empty address book if it doesn't exist
if not ADDRESS_FILE.exists():
    ADDRESS_FILE.write_text('[]')

def secure_filename_with_hangul(filename):
    """Custom secure filename function that preserves Korean characters"""
    # Encode Korean characters
    filename_encoded = urllib.parse.quote(filename)
    # Remove potentially dangerous characters but preserve Korean encoding
    filename_safe = "".join(c for c in filename_encoded 
                          if c.isalnum() or c in ['%', '-', '_', '.'])
    return filename_safe

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    files = request.files.getlist('files')
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
                    name_parts = filename.rsplit('.', 1)
                    if len(name_parts) > 1:
                        filepath = UPLOAD_FOLDER / f"{name_parts[0]}_{counter}.{name_parts[1]}"
                    else:
                        filepath = UPLOAD_FOLDER / f"{filename}_{counter}"
                
                file.save(filepath)
                
                # For display purposes, decode the filename
                display_name = urllib.parse.unquote(filepath.name)
                uploaded_files.append({
                    'path': str(filepath),
                    'name': display_name
                })
            except Exception as e:
                return jsonify({"error": f"Error saving file {file.filename}: {str(e)}"}), 500
    
    return jsonify({
        "message": "Files uploaded successfully",
        "files": uploaded_files
    })

@app.route('/api/send-email', methods=['POST'])
def send_email():
    data = request.json
    
    smtp_config = {
        "smtp_server": app.config['SMTP_SERVER'],
        "port": app.config['SMTP_PORT'],
        "sender_email": app.config['SENDER_EMAIL'],
        "password": app.config['SMTP_PASSWORD']
    }
    
    email_sender = EmailSender(smtp_config)
    result = email_sender.send_email(
        receiver_email=data['receiver_email'],
        subject=data['subject'],
        body=data['body'],
        files=[f['path'] for f in data.get('files', [])]  # Extract file paths
    )
    
    return jsonify(result)

@app.route('/api/addresses', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_addresses():
    try:
        if request.method == 'GET':
            addresses = json.loads(ADDRESS_FILE.read_text())
            return jsonify(addresses)
        
        elif request.method == 'POST':
            addresses = json.loads(ADDRESS_FILE.read_text())
            new_address = request.json
            new_address['id'] = str(len(addresses) + 1)  # Simple ID generation
            addresses.append(new_address)
            ADDRESS_FILE.write_text(json.dumps(addresses, indent=2))
            return jsonify(new_address)
        
        elif request.method == 'PUT':
            addresses = json.loads(ADDRESS_FILE.read_text())
            updated_address = request.json
            for i, addr in enumerate(addresses):
                if addr['id'] == updated_address['id']:
                    addresses[i] = updated_address
                    break
            ADDRESS_FILE.write_text(json.dumps(addresses, indent=2))
            return jsonify(updated_address)
        
        elif request.method == 'DELETE':
            address_id = request.args.get('id')
            addresses = json.loads(ADDRESS_FILE.read_text())
            addresses = [addr for addr in addresses if addr['id'] != address_id]
            ADDRESS_FILE.write_text(json.dumps(addresses, indent=2))
            return jsonify({'success': True})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 