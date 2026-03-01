from flask import Flask, jsonify, request
import csv
from collections import Counter
import random

app = Flask(__name__)

HISTORY_FILE = "539_history.csv"
history = []


# ===============================
# 讀取本地歷史資料
# ===============================
def load_history():
    global history
    history.clear()

    try:
        with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # 跳過標題

            for row in reader:
                history.append({
                    "period": row[0],
                    "date": row[1],
                    "numbers": list(map(int, row[2:7]))
                })

        print("歷史資料載入完成:", len(history))

    except Exception as e:
        print("讀取歷史資料失敗:", e)


load_history()


# ===============================
# 建立權重
# ===============================
def build_weights():
    counter = Counter()
    for row in history:
        for n in row["numbers"]:
            counter[n] += 1
    return counter


# ===============================
# AI 選號
# ===============================
@app.route("/generate")
def generate():

    if not history:
        return jsonify({
            "numbers": [],
            "hot": [],
            "cold": [],
            "error": "沒有歷史資料"
        })

    counter = build_weights()
    numbers = list(range(1, 40))
    weights = [counter[n] if counter[n] > 0 else 1 for n in numbers]

    draw = sorted(random.choices(numbers, weights=weights, k=5))

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    return jsonify({
        "numbers": draw,
        "hot": hot,
        "cold": cold
    })


# ===============================
# 歷史查詢
# ===============================
@app.route("/history")
def history_query():

    period = request.args.get("period")

    if not period:
        return jsonify({"error": "請提供期數"}), 400

    for row in history:
        if row["period"] == period:
            return jsonify(row)

    return jsonify({"error": "查無此期數"}), 404


# ===============================
# 手動重新載入資料
# ===============================
@app.route("/reload")
def reload_data():
    load_history()
    return jsonify({
        "status": "reloaded",
        "records": len(history)
    })


@app.route("/")
def home():
    return "539來財 商業穩定版運行中"


if __name__ == "__main__":
    app.run()
