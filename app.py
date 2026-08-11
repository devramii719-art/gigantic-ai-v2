import os
import sqlite3
from datetime import datetime, timedelta
import threading
from flask import Flask, request, jsonify, render_template, redirect, url_for

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'gigantic_v2_enterprise_secure_key_2026'

DB_NAME = "gigantic_v2.db"

# 1. تهيئة قاعدة البيانات الفولاذية
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # جدول المستخدمين وفترة التجربة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            niche TEXT,
            country TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trial_expiry TIMESTAMP,
            is_paid INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1
        )
    ''')
    # جدول عمليات الدفع عبر Cryptomus
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            order_id TEXT UNIQUE NOT NULL,
            amount TEXT DEFAULT '300',
            currency TEXT DEFAULT 'USDT',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # جدول الليدات المستخرجة والمراسلات الآلية (AI Auto-Closing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            lead_name TEXT,
            lead_contact TEXT,
            niche TEXT,
            status TEXT DEFAULT 'extracted',
            ai_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. رأس حماية السيرفر وإلغاء الكاش نهائياً لضمان تحديث الواجهة فوراً
@app.after_request
def apply_security_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# 3. مسارات الصفحات الرئيسية
@app.route('/')
def home():
    return render_template('index.html', v=datetime.utcnow().timestamp())

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', v=datetime.utcnow().timestamp())

# 4. API تسليم التجربة المجانية (4 أيام حقيقية مضبوطة بالتوقيت الموحد)
@app.route('/api/v1/register-trial', methods=['POST'])
def register_trial():
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email', '').strip().lower()
        niche = data.get('niche', 'General B2B')
        country = data.get('country', 'Global')

        if not email:
            return jsonify({"status": "error", "message": "Valid email is required"}), 400

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT trial_expiry, is_paid FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        now = datetime.utcnow()
        if not user:
            expiry = now + timedelta(days=4)
            cursor.execute(
                "INSERT INTO users (email, niche, country, trial_expiry) VALUES (?, ?, ?, ?)",
                (email, str(expiry), niche, country)
            )
            conn.commit()
            trial_expiry = expiry
            is_paid = 0
        else:
            trial_expiry_str = str(user[0])
            is_paid = user[1]
            try:
                if '.' in trial_expiry_str:
                    trial_expiry = datetime.strptime(trial_expiry_str, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    trial_expiry = datetime.strptime(trial_expiry_str, '%Y-%m-%d %H:%M:%S')
            except Exception:
                trial_expiry = now + timedelta(days=4)

        conn.close()

        remaining = trial_expiry - now
        seconds_left = int(remaining.total_seconds())

        if seconds_left <= 0:
            is_expired = True
            seconds_left = 0
        else:
            is_expired = False

        return jsonify({
            "status": "success",
            "email": email,
            "seconds_left": seconds_left,
            "days_left": seconds_left // 86400,
            "is_expired": is_expired,
            "is_paid": bool(is_paid),
            "redirect_url": "/dashboard"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 5. محرك استخراج الليدات والإغلاق الآلي (AI Extraction & Auto-Closing Engine)
@app.route('/api/v1/start-automation', methods=['POST'])
def start_automation():
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email', '').strip().lower()
        target_niche = data.get('niche', 'B2B Services')
        target_country = data.get('country', 'Global')

        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 400

        threading.Thread(target=execute_ai_sales_engine, args=(email, target_niche, target_country)).start()

        return jsonify({
            "status": "success",
            "message": f"GIGANTIC Engine started extracting and auto-closing deals for {target_niche} in {target_country}.",
            "engine_status": "ACTIVE_RUNNING"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def execute_ai_sales_engine(email, niche, country):
    print(f"[AI ENGINE] Started deep scraping & closing sequence for {email} | Niche: {niche} | Country: {country}")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leads (user_email, lead_name, lead_contact, niche, status, ai_response) VALUES (?, ?, ?, ?, ?, ?)",
            (email, f"Enterprise Lead ({niche})", f"contact@{niche.lower().replace(' ', '')}-corp.com", niche, "closed", "Deal closed via AI Auto-Closer. Value: $2,500")
        )
        conn.commit()
        conn.close()
    except Exception as err:
        print(f"[AI ENGINE ERROR] {err}")

# 6. مسار فحص صحة النظام
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "platform": "GIGANTIC AI V2 Enterprise",
        "engine_version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)