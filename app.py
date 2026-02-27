from flask import Flask, jsonify
import csv
import random
from collections import Counter

app = Flask(__name__)

HISTORY_FILE = "539_history.csv"

# 啟動時讀取一次
history = []

def load_history():
    global history
    with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        history = [list(map(int, row[2:7])) for row in reader]

load_history()

def analyze():

    counter = Counter()

    # 🅱 最近50期衰減模型
    recent = history[-50:]
    for idx, draw in enumerate(recent):
        weight = (idx + 1) / 50  # 越近權重越高
        for num in draw:
            counter[num] += weight * 2

    # 🅰 遺漏值模型
    last_seen = {n: 0 for n in range(1, 40)}

    for i, draw in enumerate(reversed(history)):
        for n in range(1, 40):
            if n in draw:
                if last_seen[n] == 0:
                    last_seen[n] = i

    for n in range(1, 40):
        miss = last_seen[n]
        counter[n] += miss * 0.3  # 遺漏加權

    # 熱門 / 冷門
    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    # AI選號
    numbers = list(range(1, 40))
    weights = [counter.get(n, 1) for n in numbers]
    selected = random.choices(numbers, weights=weights, k=5)

    return sorted(list(set(selected)))[:5], hot, cold

@app.route("/generate")
def generate():
    nums, hot, cold = analyze()
    return jsonify({
        "numbers": nums,
        "hot": hot,
        "cold": cold
    })

@app.route("/")
def home():
    return "539 Cloud AI Pro Running"

if __name__ == "__main__":
    app.run()
