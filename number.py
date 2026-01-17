import json
import os

FILE = "number.json"

def load_numbers():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_numbers(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def take_number(country: str):
    data = load_numbers()

    if country not in data or len(data[country]) == 0:
        return None

    number = data[country].pop(0)  # 1 ta nomerni oladi
    save_numbers(data)
    return number
