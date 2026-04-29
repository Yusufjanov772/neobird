from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app) # Netlify'dan keladigan ma'lumotlarni qabul qilish uchun

DB_PATH = '/home/yusufkahan/bot_data.db'

# 🟢 TEXNIK REJIM HOLATINI TEKSHIRISH UCHUN API 🟢
@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
        cursor.execute('SELECT value FROM settings WHERE key="maintenance"')
        res = cursor.fetchone()
        maintenance = True if (res and res[0] == 'on') else False
        conn.close()
        return jsonify({"maintenance": maintenance}), 200
    except Exception as e:
        return jsonify({"maintenance": False, "error": str(e)}), 200

# 🟢 REKORDLARNI SAQLASH UCHUN API 🟢
@app.route('/api/record', methods=['POST'])
def save_record():
    data = request.json
    user_id = data.get('user_id')
    first_name = data.get('first_name')
    username = data.get('username')
    score = data.get('score')

    if not user_id or score is None:
        return jsonify({"error": "Ma'lumot to'liq emas"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT best_score FROM players WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute('INSERT INTO players (user_id, first_name, username, best_score) VALUES (?, ?, ?, ?)',
                           (user_id, first_name, username, score))
        else:
            if score > result[0]:
                cursor.execute('UPDATE players SET best_score = ?, first_name = ?, username = ? WHERE user_id = ?',
                               (score, first_name, username, user_id))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500