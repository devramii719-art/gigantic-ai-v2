import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'GIGANTIC_ALIEN_SWARM_SECRET_2026'

# إعداد SocketIO مع دعم WebSocket المباشر
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# اسم قاعدة البيانات المحلية
DB_FILE = 'gigantic_database.db'

def init_db():
    """إنشاء الجدول في SQLite إذا لم يكن موجوداً"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            niche TEXT,
            country TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند تشغيل السيرفر
init_db()

@app.route('/')
def home():
    """عرض الواجهة الرئيسية"""
    return render_template('index.html')

@app.route('/api/v1/auth/register', methods=['POST'])
def register_user():
    """مسار تسجيل المستخدمين والحفظ في الداتابيز"""
    data = request.get_json() or {}
    email = data.get('email')
    niche = data.get('niche', 'General')
    country = data.get('country', 'Global')

    if not email:
        return jsonify({'status': 'error', 'message': 'البريد الإلكتروني مطلوب'}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (email, niche, country) VALUES (?, ?, ?)", (email, niche, country))
        conn.commit()
        
        # جلب العدد الإجمالي للمسجلين
        cursor.execute("SELECT COUNT(*) FROM users")
        total_count = cursor.fetchone()[0]
        conn.close()

        # بث التحديث المباشر لكل المستخدمين المصلين بـ SocketIO
        socketio.emit('lead_updated', {
            'total': total_count, 
            'latest_email': email,
            'niche': niche,
            'country': country
        })

        return jsonify({
            'status': 'success', 
            'message': f'تم حفظ الحساب {email} بنجاح!', 
            'total': total_count
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/v1/auth/stats', methods=['GET'])
def get_stats():
    """مسار جلب الإحصائيات وآخر المسجلين"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT email, niche, country, created_at FROM users ORDER BY id DESC LIMIT 5")
        latest_users = cursor.fetchall()
        conn.close()

        users_list = []
        for u in latest_users:
            users_list.append({
                'email': u[0],
                'niche': u[1],
                'country': u[2],
                'created_at': u[3]
            })

        return jsonify({'total': total_count, 'users': users_list})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print("🛸 Alien Terminal Connected!")
    emit('system_response', {'data': 'متصل بنجاح مع سيرفر GIGANTIC AI'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)