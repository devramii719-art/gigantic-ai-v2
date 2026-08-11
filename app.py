from gevent import monkey
monkey.patch_all()

import os
import json
import time
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'GIGANTIC_ALIEN_SWARM_SECRET_2026')

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# قائمة الـ 20 لغة
LANGUAGES = [
    {"code": "ar-DZ", "name": "🇩🇿 العربية (الجزائر)"},
    {"code": "ar-SA", "name": "🇸🇦 العربية (السعودية)"},
    {"code": "ar-AE", "name": "🇦🇪 العربية (الإمارات)"},
    {"code": "ar-EG", "name": "🇪🇬 العربية (مصر)"},
    {"code": "en-US", "name": "🇺🇸 English (US)"},
    {"code": "en-GB", "name": "🇬🇧 English (UK)"},
    {"code": "fr-FR", "name": "🇫🇷 Français"},
    {"code": "es-ES", "name": "🇪🇸 Español"},
    {"code": "de-DE", "name": "🇩🇪 Deutsch"},
    {"code": "zh-CN", "name": "🇨🇳 中文 (Mandarin)"},
    {"code": "ru-RU", "name": "🇷🇺 Русский"},
    {"code": "tr-TR", "name": "🇹🇷 Türkçe"},
    {"code": "pt-BR", "name": "🇧🇷 Português"},
    {"code": "it-IT", "name": "🇮🇹 Italiano"},
    {"code": "ja-JP", "name": "🇯🇵 日本語"},
    {"code": "ko-KR", "name": "🇰🇷 한국어"},
    {"code": "hi-IN", "name": "🇮🇳 हिन्दी"},
    {"code": "ur-PK", "name": "🇵🇰 اردو"},
    {"code": "id-ID", "name": "🇮🇩 Bahasa Indonesia"},
    {"code": "nl-NL", "name": "🇳🇱 Nederlands"}
]

class MemoryAgent:
    def __init__(self, db_path="gigantic_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vector_id TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    niche TEXT,
                    country TEXT,
                    interaction_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON memory_logs(email)")
            conn.commit()

    def save_context(self, email, interaction_type, payload, niche="", country=""):
        timestamp = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory_logs")
            count = cursor.fetchone()[0] + 1
            vector_id = f"vec_{count}"

            cursor.execute("""
                INSERT INTO memory_logs (vector_id, email, niche, country, interaction_type, payload, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (vector_id, email, niche, country, interaction_type, json.dumps(payload, ensure_ascii=False), timestamp))
            conn.commit()
            return vector_id

    def semantic_query(self, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memory_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["payload"] = json.loads(item["payload"])
                results.append(item)
            return results

memory = MemoryAgent()

@app.route('/')
def index():
    return render_template('index.html', languages=LANGUAGES)

@app.route('/dashboard')
def dashboard():
    """مسار لوحة التحكم لعرض السجلات وتفادي خطأ 404"""
    logs = memory.semantic_query(limit=50)
    return jsonify({
        "status": "DASHBOARD_ACTIVE",
        "system": "GIGANTIC AI SWARM 2026",
        "total_saved_leads": len(logs),
        "recent_memory_logs": logs
    }), 200

@app.route('/healthz', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "GIGANTIC AI Swarm 2026"}), 200

@app.route('/api/v1/swarm/run', methods=['POST'])
def run_full_swarm():
    try:
        data = request.get_json(force=True) or {}
        email = data.get('email')
        niche = data.get('niche', 'General')
        country = data.get('country', 'Global')
        lang = data.get('lang', 'ar-DZ')

        if not email:
            return jsonify({"status": "ERROR", "message": "يرجى إدخال البريد الإلكتروني"}), 400

        # حفظ البيانات فوراً في قاعدة SQLite
        memory.save_context(email, "TRIAL_REGISTRATION", {
            "email": email,
            "niche": niche,
            "country": country,
            "language": lang,
            "swarm_status": "ACTIVATED",
            "trial_period": "4_DAYS_FREE"
        }, niche=niche, country=country)

        return jsonify({
            "status": "SUCCESS",
            "message": "تم حفظ بيانات شركتك في الذاكرة وتفعيل شبكة الوكلاء بنجاح!",
            "email": email
        }), 200

    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@socketio.on('realtime_stream_ping')
def handle_realtime_ping(data):
    country = data.get('country', 'Global') if isinstance(data, dict) else 'Global'
    emit('realtime_stream_pong', {
        "avatar_status": "SPEAKING_LIP_SYNC",
        "globe_pulse": True,
        "latency_ms": 120,
        "logs": f"[SWARM] Agent Hunter active for target country: {country}"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)