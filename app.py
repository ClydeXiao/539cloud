from flask import Flask, jsonify, request
import csv
import random
from collections import Counter
import os

app = Flask(__name__)

HISTORY_FILE = "539_history.csv"
history = []

####################################################
# 讀取歷史資料
####################################################

def load_history():
    global history
    history = []

    if not os.path.exists(HISTORY_FILE):
        return

    with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳過標題列
        history = [row for row in reader]


load_history()

####################################################
# 建立權重
####################################################

def build_weights():

    if not history:
        return None

    counter = Counter()
    last_seen = {n: None for n in range(1, 40)}
    total_draws = len(history)

    for idx, row in enumerate(history):
        numbers = list(map(int, row[2:7]))
        for num in numbers:
            counter[num] += 1
            last_seen[num] = idx

    # 最近50期加權
    for row in history[-50:]:
        numbers = list(map(int, row[2:7]))
        for num in numbers:
            counter[num] += 2

    # 遺漏值加權
    for n in range(1, 40):
        if last_seen[n] is not None:
            miss = total_draws - last_seen[n]
            counter[n] += miss * 0.2

    return counter

####################################################
# 不重複加權抽號
####################################################

def weighted_sample_without_replacement(counter, k=5):

    numbers = list(range(1, 40))
    weights = [counter.get(n, 1) for n in numbers]

    selected = []
    temp_numbers = numbers.copy()
    temp_weights = weights.copy()

    for _ in range(k):

        total = sum(temp_weights)
        if total <= 0:
            break

        r = random.uniform(0, total)
        upto = 0

        for i, w in enumerate(temp_weights):
            upto += w
            if upto >= r:
                selected.append(temp_numbers[i])
                temp_numbers.pop(i)
                temp_weights.pop(i)
                break

    return sorted(selected)

####################################################
# API：產生號碼
####################################################

@app.route("/generate")
def generate():

    counter = build_weights()

    if not counter:
        # 如果沒資料，隨機不重複抽
        numbers = sorted(random.sample(range(1, 40), 5))
        return jsonify({
            "numbers": numbers,
            "hot": [],
            "cold": [],
            "mode": "random_no_history"
        })

    numbers = weighted_sample_without_replacement(counter)

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    return jsonify({
        "numbers": numbers,
        "hot": hot,
        "cold": cold
    })

####################################################
# API：查詢歷史期數
####################################################

@app.route("/history")
def history_query():

    period = request.args.get("period")

    if not period:
        return jsonify({"error": "missing period"}), 400

    for row in history:
        if row[0] == period:
            return jsonify({
                "period": row[0],
                "date": row[1],
                "numbers": list(map(int, row[2:7]))
            })

    return jsonify({"error": "period not found"}), 404

####################################################
# API：最新一期
####################################################

@app.route("/latest")
def latest():

    if not history:
        return jsonify({"error": "no data"}), 404

    latest_row = history[0]

    return jsonify({
        "period": latest_row[0],
        "date": latest_row[1],
        "numbers": list(map(int, latest_row[2:7]))
    })

####################################################
# API：重新讀取 CSV
####################################################

@app.route("/update")
def update():

    load_history()
    return jsonify({
        "records": len(history),
        "status": "reloaded"
    })

####################################################
# 首頁
####################################################

@app.route("/")
def home():
    return "539 Cloud AI Stable Running"


if __name__ == "__main__":
    app.run()
