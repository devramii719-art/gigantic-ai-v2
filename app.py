import os
import sqlite3
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'gigantic_v2_ultra_secure_key_2026'

DB_NAME = "gigantic_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_uuid TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            niche TEXT,
            country TEXT,
            language TEXT DEFAULT 'ar',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trial_expiry TIMESTAMP,
            is_paid INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS target_companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            company_name TEXT NOT NULL,
            decision_maker TEXT NOT NULL,
            deal_value TEXT NOT NULL,
            strategy TEXT NOT NULL,
            status TEXT DEFAULT 'In Progress',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.after_request
def apply_security_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    return response

@app.route('/')
def home():
    return render_template('index.html', v=datetime.utcnow().timestamp())

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', v=datetime.utcnow().timestamp())

@app.route('/api/v1/auth-session', methods=['POST'])
def auth_session():
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = data.get('email', '').strip().lower()
        niche = data.get('niche', 'Software & Tech')
        country = data.get('country', 'USA')
        lang = data.get('language', 'ar')

        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT user_uuid, trial_expiry, is_paid FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        now = datetime.utcnow()
        if not user:
            user_uuid = str(uuid.uuid4())
            expiry = now + timedelta(days=4)
            cursor.execute(
                "INSERT INTO users (user_uuid, email, niche, country, language, trial_expiry) VALUES (?, ?, ?, ?, ?, ?)",
                (user_uuid, email, niche, country, lang, str(expiry))
            )
            # إضافة بيانات توضيحية للعميل
            targets = [
                (email, f"Apex {niche} Corp", "David Miller (CEO)", "$3,500", "Aggressive Pitch", "Closed"),
                (email, f"Global {country} Logistics", "Elena Rostova (VP Sales)", "$5,000", "Consultative Negotiation", "In Progress"),
                (email, f"Vance Capital {niche}", "Marcus Vance (Managing Director)", "$2,800", "Value Proposal", "Closed")
            ]
            cursor.executemany(
                "INSERT INTO target_companies (user_email, company_name, decision_maker, deal_value, strategy, status) VALUES (?, ?, ?, ?, ?, ?)",
                targets
            )
            conn.commit()
            trial_expiry = expiry
            is_paid = 0
        else:
            user_uuid = user[0]
            trial_expiry_str = str(user[1])
            is_paid = user[2]
            cursor.execute("UPDATE users SET language = ?, niche = ?, country = ? WHERE email = ?", (lang, niche, country, email))
            conn.commit()
            try:
                trial_expiry = datetime.strptime(trial_expiry_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
            except Exception:
                trial_expiry = now + timedelta(days=4)

        conn.close()

        remaining = trial_expiry - now
        seconds_left = max(0, int(remaining.total_seconds()))

        return jsonify({
            "status": "success",
            "user_uuid": user_uuid,
            "email": email,
            "niche": niche,
            "country": country,
            "seconds_left": seconds_left,
            "is_expired": seconds_left <= 0,
            "is_paid": bool(is_paid)
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/get-targets', methods=['POST'])
def get_targets():
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = data.get('email', '').strip().lower()

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT company_name, decision_maker, deal_value, strategy, status FROM target_companies WHERE user_email = ?", (email,))
        rows = cursor.fetchall()
        conn.close()

        targets = []
        for r in rows:
            targets.append({
                "company_name": r[0],
                "decision_maker": r[1],
                "deal_value": r[2],
                "strategy": r[3],
                "status": r[4]
            })

        return jsonify({"status": "success", "targets": targets}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)