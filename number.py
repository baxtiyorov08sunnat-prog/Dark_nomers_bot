import json
import random

JSON_FILE = "number.json"


def load_numbers():
    """JSON faylni o‘qish"""
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_countries():
    """Mavjud country lar ro‘yxati"""
    data = load_numbers()
    return list(data.keys())


def get_price(country):
    """Country bo‘yicha narx"""
    data = load_numbers()
    return data[country]["price"]


def get_random_number(country):
    """
    Country bo‘yicha bitta nomer berish
    Agar nomer qolmagan bo‘lsa -> None
    """
    data = load_numbers()

    numbers = data[country]["numbers"]
    if not numbers:
        return None

    number = random.choice(numbers)
    return number
