import os
import sqlite3
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-this')
DB_PATH = 'licenses.db'

# ==================== دیتابیس ====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hardware_id TEXT UNIQUE,
            license_key TEXT,
            activated_at TEXT,
            expires_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==================== توابع کمکی ====================
def generate_license(hardware_id):
    message = hardware_id + datetime.now().isoformat()
    digest = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return 'LIC-' + digest[:4] + '-' + digest[4:8] + '-' + digest[8:12] + '-' + digest[12:16]

def is_license_valid(license_key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT hardware_id, expires_at, is_active FROM licenses
        WHERE license_key = ?
    ''', (license_key,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return False, None
    
    hardware_id, expires_at, is_active = row
    
    if not is_active:
        return False, hardware_id
    
    if expires_at:
        expires = datetime.fromisoformat(expires_at)
        if datetime.now() > expires:
            return False, hardware_id
    
    return True, hardware_id

# ==================== API ====================
@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if not data or 'hardware_id' not in data:
        return jsonify({'error': 'Missing hardware_id'}), 400
    
    hardware_id = data['hardware_id']
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT license_key FROM licenses WHERE hardware_id = ?', (hardware_id,))
    existing = c.fetchone()
    
    if existing:
        conn.close()
        return jsonify({
            'success': False,
            'message': 'This hardware already has a license.',
            'license_key': existing[0]
        })
    
    license_key = generate_license(hardware_id)
    expires_at = (datetime.now() + timedelta(days=365)).isoformat()
    
    c.execute('''
        INSERT INTO licenses (hardware_id, license_key, activated_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, 1)
    ''', (hardware_id, license_key, datetime.now().isoformat(), expires_at))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'license_key': license_key,
        'expires_at': expires_at,
        'hardware_id': hardware_id
    })

@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.get_json()
    if not data or 'license_key' not in data:
        return jsonify({'error': 'Missing license_key'}), 400
    
    license_key = data['license_key']
    valid, hardware_id = is_license_valid(license_key)
    
    if valid:
        return jsonify({
            'valid': True,
            'message': 'License is valid.',
            'hardware_id': hardware_id
        })
    else:
        return jsonify({
            'valid': False,
            'message': 'License is invalid or expired.'
        })

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({'status': 'running', 'version': '1.0.0'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)