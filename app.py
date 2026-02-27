from flask import Flask, jsonify
import csv
import random
from collections import Counter

app = Flask(__name__)

HISTORY_FILE = "539_history.csv"


def load_history():
    history = []
    try:
        with open(HISTORY_FILE, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            for row in reader:
                numbers = list(map(int, row[2:7]))
                history.append(numbers)
    except:
        pass
    return history


def generate_numbers():
    history = load_history()
    counter = Counter()

    for draw in history:
        counter.update(draw)

    numbers = list(range(1, 40))
    weights = [counter.get(n, 1) for n in numbers]

    selected = random.choices(numbers, weights=weights, k=5)
    return sorted(list(set(selected)))[:5]


@app.route("/generate")
def generate():
    nums = generate_numbers()
    return jsonify({
        "numbers": nums
    })


@app.route("/")
def home():
    return "539 Cloud API Running"


if __name__ == "__main__":
    app.run()