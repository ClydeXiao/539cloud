from flask import Flask, jsonify, request
import requests
from collections import Counter
import random

app = Flask(__name__)

history = []

TAIWAN_API = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result"

def fetch_latest():
    global history

    url = f"{TAIWAN_API}?period&startMonth=2025-01&endMonth=2026-12"
    r = requests.get(url, timeout=10)

    if r.status_code == 200:
        data = r.json()
        history.clear()

        for item in data["content"]["daily539Res"]:
            history.append({
                "period": str(item["period"]),
                "date": item["lotteryDate"][:10],
                "numbers": item["drawNumberAppear"]
            })

fetch_latest()

def build_weights():
    counter = Counter()

    for row in history:
        for n in row["numbers"]:
            counter[n] += 1

    return counter

@app.route("/generate")
def generate():

    fetch_latest()  # 每次呼叫都自動更新

    counter = build_weights()
    numbers = list(range(1, 40))
    weights = [counter[n] for n in numbers]

    draw = random.choices(numbers, weights=weights, k=5)
    draw = sorted(draw)

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    return jsonify({
        "numbers": draw,
        "hot": hot,
        "cold": cold
    })

@app.route("/history")
def history_query():

    fetch_latest()  # 自動更新

    period = request.args.get("period")

    for row in history:
        if row["period"] == period:
            return jsonify(row)

    return jsonify({"error": "period not found"}), 404

@app.route("/")
def home():
    return "539來財 正式自動更新版運行中"

if __name__ == "__main__":
    app.run()
