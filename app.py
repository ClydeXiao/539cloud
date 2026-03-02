from flask import Flask, jsonify, request
import sqlite3
import csv
import random
import requests
from collections import Counter
from datetime import datetime

app = Flask(__name__)
DB_FILE = "history.db"

############################################################
# 初始化資料庫
############################################################

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        period TEXT PRIMARY KEY,
        date TEXT,
        n1 INTEGER,
        n2 INTEGER,
        n3 INTEGER,
        n4 INTEGER,
        n5 INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS ai_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        mode TEXT,
        numbers TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

############################################################
# CSV 匯入
############################################################

@app.route("/import_csv")
def import_csv():

    try:
        with open("539_history.csv", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            count = 0
            for row in reader:
                try:
                    c.execute("""
                    INSERT OR IGNORE INTO history
                    VALUES (?,?,?,?,?,?,?)
                    """, (
                        row[0],
                        row[1],
                        int(row[2]),
                        int(row[3]),
                        int(row[4]),
                        int(row[5]),
                        int(row[6])
                    ))
                    count += 1
                except:
                    pass

            conn.commit()
            conn.close()

        return jsonify({"imported": count})

    except Exception as e:
        return jsonify({"error": str(e)})

############################################################
# 官方 API 自動更新
############################################################

@app.route("/auto_update")
def auto_update():

    try:
        url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result"
        params = {
            "startMonth": "2025-01",
            "endMonth": datetime.now().strftime("%Y-%m")
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        count = 0

        for item in data.get("content", {}).get("daily539Res", []):
            period = str(item["period"])
            date = item["lotteryDate"][:10]
            nums = item["drawNumberAppear"]

            c.execute("""
            INSERT OR IGNORE INTO history
            VALUES (?,?,?,?,?,?,?)
            """, (
                period,
                date,
                nums[0],
                nums[1],
                nums[2],
                nums[3],
                nums[4]
            ))
            count += 1

        conn.commit()
        conn.close()

        return jsonify({"updated": count})

    except Exception as e:
        return jsonify({"error": str(e)})

############################################################
# 取得全部資料
############################################################

def get_all_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY period")
    rows = c.fetchall()
    conn.close()
    return rows

############################################################
# AI 權重
############################################################

def build_weights():
    rows = get_all_history()
    counter = Counter()

    for row in rows:
        for n in row[2:7]:
            counter[n] += 1

    return counter

############################################################
# AI 產生
############################################################

def generate_numbers(mode="balanced"):

    counter = build_weights()
    numbers = list(range(1,40))

    if not counter:
        return sorted(random.sample(numbers,5)), [], []

    weights = []

    for n in numbers:
        w = counter[n]

        if mode == "aggressive":
            w *= 1.5
        elif mode == "cold":
            w = max(counter.values()) - w + 1

        weights.append(max(w,1))

    selected = random.sample(
        random.choices(numbers, weights=weights, k=20),
        5
    )

    hot = [n for n,_ in counter.most_common(5)]
    cold = [n for n,_ in counter.most_common()[:-6:-1]]

    return sorted(selected), hot, cold

############################################################
# API 產生
############################################################

@app.route("/generate")
def generate():
    mode = request.args.get("mode","balanced")
    numbers, hot, cold = generate_numbers(mode)

    return jsonify({
        "numbers": numbers,
        "hot": hot,
        "cold": cold,
        "mode": mode
    })

############################################################
# AI 紀錄保存
############################################################

@app.route("/save_ai")
def save_ai():

    mode = request.args.get("mode")
    numbers = request.args.get("numbers")

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
    INSERT INTO ai_logs (created_at, mode, numbers)
    VALUES (?,?,?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        mode,
        numbers
    ))

    conn.commit()
    conn.close()

    return jsonify({"saved": True})

@app.route("/ai_logs")
def ai_logs():

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM ai_logs ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()

    return jsonify(rows)

############################################################
# 其他 API
############################################################

@app.route("/history")
def history_query():
    period = request.args.get("period")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM history WHERE period=?", (period,))
    row = c.fetchone()
    conn.close()

    if row:
        return jsonify({
            "period": row[0],
            "date": row[1],
            "numbers": list(row[2:7])
        })

    return jsonify({"error":"not found"}),404

@app.route("/recent")
def recent():
    limit = int(request.args.get("limit",10))
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY period DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "period": row[0],
            "date": row[1],
            "numbers": list(row[2:7])
        })

    return jsonify(result)

@app.route("/latest")
def latest():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY period DESC LIMIT 1")
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error":"no data"}),404

    return jsonify({
        "period": row[0],
        "date": row[1],
        "numbers": list(row[2:7])
    })

@app.route("/trend")
def trend():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY period DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()

    counter = Counter()
    for row in rows:
        for n in row[2:7]:
            counter[n]+=1

    return jsonify(counter)

@app.route("/")
def home():
    return "539來財 Pro 商業級 SQLite Cloud Running"

############################################################

if __name__ == "__main__":
    app.run()
