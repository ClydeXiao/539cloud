from flask import Flask, jsonify, request
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

def build_weights():

    counter = Counter()
    last_seen = {n: None for n in range(1, 40)}
    total_draws = len(history)

    for idx, draw in enumerate(history):
        for num in draw:
            counter[num] += 1
            last_seen[num] = idx

    # 最近20期趨勢評估（動態調整）
    trend_score = Counter()
    for draw in history[-20:]:
        for num in draw:
            trend_score[num] += 1

    trend_factor = 1 + (sum(trend_score.values()) / 100)

    # 最近50期加權
    for draw in history[-50:]:
        for num in draw:
            counter[num] += 2 * trend_factor

    # 遺漏值（動態強度）
    for n in range(1, 40):
        if last_seen[n] is not None:
            miss = total_draws - last_seen[n]
            counter[n] += miss * 0.15 * trend_factor

    return counter

def monte_carlo(counter, mode="stable"):

    numbers = list(range(1, 40))

    if mode == "aggressive":
        weights = [counter[n] ** 1.5 for n in numbers]
    elif mode == "cold":
        weights = [(max(counter.values()) - counter[n] + 1) for n in numbers]
    else:
        weights = [counter[n] for n in numbers]

    simulation_counter = Counter()

    # 🔥 300次模擬（仍安全）
    for _ in range(300):
        draw = random.choices(numbers, weights=weights, k=5)
        for n in draw:
            simulation_counter[n] += 1

    best = [n for n, _ in simulation_counter.most_common(5)]

    return sorted(best), simulation_counter

@app.route("/generate")
def generate():

    mode = request.args.get("mode", "stable")

    counter = build_weights()

    selected, mc_counter = monte_carlo(counter, mode)

    total_weight = sum(counter.values())

    probabilities = {
        n: round((counter[n] / total_weight) * 100, 2)
        for n in range(1, 40)
    }

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    return jsonify({
        "numbers": selected,
        "hot": hot,
        "cold": cold,
        "probabilities": probabilities,
        "mc_frequency": dict(mc_counter)
    })

@app.route("/")
def home():
    return "539 Cloud AI Adaptive Running"

if __name__ == "__main__":
    app.run()
