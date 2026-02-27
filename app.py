from flask import Flask, jsonify
import csv
import random
from collections import Counter

app = Flask(__name__)

HISTORY_FILE = "539_history.csv"

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
    last_seen = {n: None for n in range(1, 40)}

    total_draws = len(history)

    # 單次掃描（高效能）
    for idx, draw in enumerate(history):
        for num in draw:
            counter[num] += 1
            last_seen[num] = idx

    # 最近50期加權
    for draw in history[-50:]:
        for num in draw:
            counter[num] += 2

    # 遺漏值加權
    for n in range(1, 40):
        if last_seen[n] is not None:
            miss = total_draws - last_seen[n]
            counter[n] += miss * 0.2

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

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
    return "539 Cloud AI Optimized Running"

if __name__ == "__main__":
    app.run()
