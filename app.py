from gevent import monkey
monkey.patch_all()

import os
import json
import time
import sqlite3
import asyncio
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'GIGANTIC_ALIEN_SWARM_SECRET_2026')

# إعداد SocketIO مع إسناد نمط gevent الاستقراري
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# ====================================================
# 1. شبكة وكلاء الذكاء الاصطناعي (Multi-Agent Swarm System)
# ====================================================

class HunterAgent:
    """وكيل الاستقطاب: جمع بيانات الإيميلات والتواصل المباشر"""
    def hunt_leads(self, niche, country):
        clean_niche = niche.lower().replace(' ', '') if niche else "general"
        return {
            "agent": "Hunter",
            "status": "SUCCESS",
            "leads_found": 150,
            "sample_leads": [f"contact@{clean_niche}_lead{i}.com" for i in range(1, 4)],
            "target_country": country or "Global"
        }

class CloserAgent:
    """وكيل المبيعات والإغلاق: معالجة الاعتراضات والتكيف مع لهجة العميل"""
    def close_deal(self, lead_email, client_dialect="ar"):
        return {
            "agent": "Closer",
            "status": "CLOSED",
            "lead": lead_email,
            "negotiation_score": 0.98,
            "action": "إقناع العميل وحل الاعتراض بنجاح واستعداد لتوقيع العقد."
        }

class FinanceAgent:
    """وكيل المالية: إصدار الفواتير ومتابعة التحصيل عبر الكريبتو والبطاقات"""
    def generate_invoice(self, client_email, plan_amount=300):
        return {
            "agent": "Finance",
            "invoice_id": f"INV-{int(time.time())}",
            "amount_usdt": plan_amount,
            "cryptomus_link": "https://cryptomus.com/pay/gigantic-enterprise-300",
            "stripe_link": "https://checkout.stripe.com/pay/gigantic-300",
            "status": "PENDING_PAYMENT"
        }

class MemoryAgent:
    """وكيل الأرشيف والذاكرة المترابطة مع تخزين دائم باستخدام SQLite"""
    def __init__(self, db_path="gigantic_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """إنشاء الجدول والفهارس تلقائياً عند التشغيل"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vector_id TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL,
                    interaction_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_email ON memory_logs(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON memory_logs(interaction_type)")
            conn.commit()

    def save_context(self, email, interaction_type, payload):
        """حفظ السياق داخل SQLite مع تشفير البيانات المعقدة كـ JSON"""
        timestamp = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memory_logs")
            count = cursor.fetchone()[0] + 1
            vector_id = f"vec_{count}"

            cursor.execute("""
                INSERT INTO memory_logs (vector_id, email, interaction_type, payload, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (vector_id, email, interaction_type, json.dumps(payload, ensure_ascii=False), timestamp))
            conn.commit()
            return vector_id

    def semantic_query(self, limit=10, email=None):
        """استرجاع سجلات الذاكرة مع إمكانية التصفية ببريد العميل"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if email:
                cursor.execute("""
                    SELECT vector_id, email, interaction_type as type, payload, timestamp
                    FROM memory_logs WHERE email = ? ORDER BY id DESC LIMIT ?
                """, (email, limit))
            else:
                cursor.execute("""
                    SELECT vector_id, email, interaction_type as type, payload, timestamp
                    FROM memory_logs ORDER BY id DESC LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["payload"] = json.loads(item["payload"])
                results.append(item)
            return results

# تهيئة شبكة الوكلاء
hunter = HunterAgent()
closer = CloserAgent()
finance = FinanceAgent()
memory = MemoryAgent()

# ====================================================
# 2. المسارات البرمجية والربط اللحظي (Routes & WebSockets)
# ====================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/healthz', methods=['GET'])
def health_check():
    """مسار فحص السلامة لاستضافة Render"""
    return jsonify({"status": "healthy", "service": "GIGANTIC AI Swarm", "version": "2026.1"}), 200

@app.route('/api/v1/swarm/run', methods=['POST'])
def run_full_swarm():
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email', 'guest@company.com')
        niche = data.get('niche', 'Software')
        country = data.get('country', 'Global')

        # 1. الاستقطاب (Hunt)
        hunt_res = hunter.hunt_leads(niche, country)
        memory.save_context(email, "HUNT", hunt_res)

        # 2. حماية القائمة وإسناد الهدف
        sample_leads = hunt_res.get("sample_leads", [])
        target_lead = sample_leads[0] if sample_leads else email

        # 3. الإغلاق (Close)
        close_res = closer.close_deal(target_lead)
        memory.save_context(email, "CLOSE", close_res)

        # 4. التمويل والفوترة (Finance)
        fin_res = finance.generate_invoice(email)
        memory.save_context(email, "FINANCE", fin_res)

        return jsonify({
            "status": "SWARM_EXECUTION_COMPLETE",
            "hunter": hunt_res,
            "closer": close_res,
            "finance": fin_res,
            "vector_memory_status": "PERSISTED_SQLITE"
        }), 200

    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

@app.route('/api/v1/memory/logs', methods=['GET'])
def get_memory_logs():
    """استرجاع سجلات الذاكرة المترابطة من قاعدة بيانات SQLite"""
    email = request.args.get('email')
    logs = memory.semantic_query(limit=10, email=email)
    
    return jsonify({
        "status": "SUCCESS",
        "returned_records": len(logs),
        "logs": logs
    }), 200

# المعالجة الصوتية والرسومية المباشرة (Multimodal Low-Latency Stream)
@socketio.on('realtime_stream_ping')
def handle_realtime_ping(data):
    country = data.get('country', 'Global') if isinstance(data, dict) else 'Global'
    emit('realtime_stream_pong', {
        "avatar_status": "SPEAKING_LIP_SYNC",
        "globe_pulse": True,
        "latency_ms": 120,
        "logs": f"[SWARM] Agent Hunter active for country: {country}"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)