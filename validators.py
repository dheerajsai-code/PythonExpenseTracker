from datetime import datetime


def parse_date(date_text):
    return datetime.strptime(date_text, "%Y-%m-%d")


def get_valid_amount(prompt):
    amount_text = input(prompt).strip()

    try:
        amount = float(amount_text)
    except ValueError:
        print("Amount must be a number.")
        return None

    if amount <= 0:
        print("Amount must be greater than 0.")
        return None

    return amount


def get_valid_date(prompt):
    date_text = input(prompt).strip()

    if not date_text:
        print("Date cannot be empty.")
        return None

    try:
        parse_date(date_text)
    except ValueError:
        print("Date must be in YYYY-MM-DD format.")
        return None

    return date_text
