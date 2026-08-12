from gevent import monkey
monkey.patch_all()

import os
import json
import time
import sqlite3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'GIGANTIC_ALIEN_SWARM_SECRET_2026')

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

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

    def semantic_query(self, limit=100):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memory_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                try:
                    item["payload"] = json.loads(item["payload"])
                except Exception:
                    pass
                results.append(item)
            return results

memory = MemoryAgent()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    logs = memory.semantic_query(limit=100)
    return jsonify({
        "status": "DASHBOARD_ACTIVE",
        "system": "GIGANTIC AI SWARM 2026",
        "total_saved_leads": len(logs),
        "recent_memory_logs": logs
    }), 200

@app.route('/api/v1/swarm/run', methods=['POST'])
def run_full_swarm():
    try:
        data = request.get_json(force=True) or {}
        email = data.get('email')
        niche = data.get('niche', 'General')
        country = data.get('country', 'Global')

        if not email or '@' not in email:
            return jsonify({"status": "ERROR", "message": "يرجى إدخال بريد إلكتروني صحيح"}), 400

        vec_id = memory.save_context(email, "REGISTERED_LEAD", {
            "email": email,
            "niche": niche,
            "country": country,
            "status": "ACTIVATED"
        }, niche=niche, country=country)

        return jsonify({
            "status": "SUCCESS",
            "message": f"تم حفظ بريدك ({email}) بنجاح في الذاكرة المترابطة (Vector ID: {vec_id})!",
            "email": email,
            "vector_id": vec_id
        }), 200

    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@socketio.on('realtime_stream_ping')
def handle_realtime_ping(data):
    country = data.get('country', 'Global') if isinstance(data, dict) else 'Global'
    emit('realtime_stream_pong', {
        "avatar_status": "SPEAKING_LIP_SYNC",
        "logs": f"[SWARM Voice Agent] Live Voice Analysis Active for: {country}"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)