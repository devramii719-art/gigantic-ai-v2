import os
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'GIGANTIC_ALIEN_SWARM_SECRET_2026'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# مسار دائم لقاعدة البيانات لعدم ضياع البيانات
DB_FILE = os.path.join(os.path.dirname(__file__), 'gigantic_database.db')

def init_db():
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

init_db()

@app.route('/')
def home():
    return render_template('index.html')

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
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (email, niche, country) VALUES (?, ?, ?)", (email, niche, country))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_count = cursor.fetchone()[0]
        conn.close()

        # بث حي لجميع المستخدمين
        socketio.emit('lead_updated', {
            'total': total_count, 
            'latest_email': email,
            'niche': niche,
            'country': country
        })

        return jsonify({'status': 'success', 'message': f'تم الحفظ بنجاح!', 'total': total_count})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/v1/auth/stats', methods=['GET'])
def get_stats():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT email, niche, country, created_at FROM users ORDER BY id DESC")
        latest_users = cursor.fetchall()
        conn.close()

        users_list = [{'email': u[0], 'niche': u[1], 'country': u[2], 'created_at': u[3]} for u in latest_users]

        return jsonify({'total': total_count, 'users': users_list})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)