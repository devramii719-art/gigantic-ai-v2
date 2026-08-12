import os
import sqlite3
import shutil
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'GIGANTIC_FULL_EXPANDED_2026'

DB_FILE = 'gigantic_database.db'

def init_db():
    """إنشاء الجداول اللازمة للحفظ الدائم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # جدول الحسابات
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            niche TEXT,
            country TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # جدول المدفوعات والعمليات
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            amount REAL,
            gateway TEXT,
            status TEXT,
            tx_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def auto_backup():
    """نسخ احتياطي لقاعدة البيانات"""
    try:
        backup_dir = 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.copy(DB_FILE, os.path.join(backup_dir, f'backup_{date_str}.db'))
    except Exception as e:
        print(f"Backup Log: {e}")

init_db()

@app.route('/')
def home():
    return render_template('index.html')

# 1. مسار تسجيل حساب جديد
@app.route('/api/v1/auth/register', methods=['POST'])
def register_user():
    data = request.get_json() or {}
    email = data.get('email')
    niche = data.get('niche', 'General')
    country = data.get('country', 'Global')

    if not email:
        return jsonify({'status': 'error', 'message': 'البريد الإلكتروني مطلوب'}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO users (email, niche, country) VALUES (?, ?, ?)", (email, niche, country))
        conn.commit()
        
        c.execute("SELECT COUNT(*) FROM users")
        total_count = c.fetchone()[0]
        conn.close()

        auto_backup()
        return jsonify({'status': 'success', 'message': f'تم حفظ الحساب {email} بنجاح!', 'total': total_count})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 2. مسار جلب الإحصائيات والحسابات للـ Export
@app.route('/api/v1/data/all', methods=['GET'])
def get_all_data():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, email, niche, country, created_at FROM users ORDER BY id DESC")
        users = c.fetchall()
        
        c.execute("SELECT id, email, amount, gateway, status, created_at FROM payments ORDER BY id DESC")
        payments = c.fetchall()
        conn.close()

        u_list = [{'id': u[0], 'email': u[1], 'niche': u[2], 'country': u[3], 'date': u[4]} for u in users]
        p_list = [{'id': p[0], 'email': p[1], 'amount': p[2], 'gateway': p[3], 'status': p[4], 'date': p[5]} for p in payments]

        return jsonify({'users': u_list, 'payments': p_list, 'total_users': len(u_list)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 3. مسارات أزرار العمليات (Run/Pause)
@app.route('/api/v1/swarm/control', methods=['POST'])
def swarm_control():
    data = request.get_json() or {}
    action = data.get('action')
    if action == 'run':
        return jsonify({'status': 'success', 'message': 'تم إطلاق شبكة الوكلاء Swarm بنجاح. جاري العمل...'})
    elif action == 'pause':
        return jsonify({'status': 'success', 'message': 'تم إيقاف العمليات مؤقتاً.'})
    return jsonify({'status': 'error', 'message': 'الإجراء غير معروف'}), 400

# 4. مسار معالجة الدفع وإصدار الفاتورة
@app.route('/api/v1/payments/create', methods=['POST'])
def create_payment():
    data = request.get_json() or {}
    email = data.get('email', 'guest@gigantic.com')
    gateway = data.get('gateway', 'Cryptomus')
    amount = float(data.get('amount', 300.0))
    tx_id = f"TX_{gateway[:3].upper()}_{int(datetime.now().timestamp())}"

    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO payments (email, amount, gateway, status, tx_id) VALUES (?, ?, ?, ?, ?)",
                  (email, amount, gateway, 'CONFIRMED', tx_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'تم تسجيل المعاملة بنجاح!', 'tx_id': tx_id, 'amount': amount})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 5. شات نصي ذكي (بديل المساعد الصوتي)
@app.route('/api/v1/chat', methods=['POST'])
def text_chat():
    data = request.get_json() or {}
    msg = data.get('message', '').strip()
    if not msg:
        return jsonify({'reply': 'يرجى كتابة أؤمرك للبدء.'})
    
    # محاكي رد متطور وخفيف جداً
    if "وكلاء" in msg or "swarm" in msg.lower():
        reply = "شبكة الوكلاء تعمل بكفاءة: Hunter يجمع البيانات، Closer يجري التفاوض، و Finance يسجل الصفقات."
    elif "دفع" in msg or "اشتراك" in msg:
        reply = "يمكنك الترقية فوراً عبر بوابات Cryptomus (USDT) أو Stripe بقيمة 300$ شهرياً."
    else:
        reply = f"تم استلام طلبك: '{msg}'. جاري تنفيذه برمجياً عبر نظام GIGANTIC AI."
    
    return jsonify({'reply': reply})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)