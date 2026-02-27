from flask import Flask, jsonify
import csv
import random
from collections import Counter

app = Flask(__name__)

HISTORY_FILE = "539_history.csv"


def load_history():
    history = []
    with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            numbers = list(map(int, row[2:7]))
            history.append(numbers)
    return history


def analyze():
    history = load_history()
    counter = Counter()

    for draw in history:
        counter.update(draw)

    hot = [n for n, _ in counter.most_common(5)]
    cold = [n for n, _ in counter.most_common()[:-6:-1]]

    # AI加權選號
    numbers = list(range(1, 40))
    weights = [counter.get(n, 1) ** 1.3 for n in numbers]
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
    return "539 Cloud AI Running"


if __name__ == "__main__":
    app.run()
