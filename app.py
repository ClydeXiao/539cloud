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
        history = [row for row in reader]

load_history()

def build_weights():
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

def monte_carlo(counter, mode="stable"):
    numbers = list(range(1, 40))

    if mode == "aggressive":
        weights = [counter[n] ** 1.5 for n in numbers]
    elif mode == "cold":
        weights = [(max(counter.values()) - counter[n] + 1) for n in numbers]
    else:
        weights = [counter[n] for n in numbers]

    simulation_counter = Counter()

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

@app.route("/history")
def history_query():
    period = request.args.get("period")

    if not period:
        return jsonify({"error": "missing period parameter"}), 400

    for row in history:
        if row[0] == period:
            return jsonify({
                "period": row[0],
                "date": row[1],
                "numbers": list(map(int, row[2:7]))
            })

    return jsonify({"error": "period not found"}), 404

@app.route("/")
def home():
    return "539 Cloud AI Final Running"

if __name__ == "__main__":
    app.run()
