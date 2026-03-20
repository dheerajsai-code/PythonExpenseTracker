from datetime import datetime

from display import print_expense_list
from storage import get_all_expenses
from validators import get_valid_date, parse_date


def show_total():
    expenses = get_all_expenses()
    total = sum(expense["amount"] for expense in expenses)
    print(f"Total spending: {total:.2f}")


def search_by_category():
    category = input("Enter category to search: ").strip()

    if not category:
        print("Category cannot be empty.")
        return

    expenses = get_all_expenses()
    matching_expenses = []

    for expense in expenses:
        if expense["category"].lower() == category.lower():
            matching_expenses.append(expense)

    if not matching_expenses:
        print("No expenses found in that category.")
        return

    print_expense_list(matching_expenses, f"Expenses in category: {category}")


def filter_by_date():
    date = get_valid_date("Enter date to filter (YYYY-MM-DD): ")
    if date is None:
        return

    expenses = get_all_expenses()
    matching_expenses = []

    for expense in expenses:
        if expense["date"] == date:
            matching_expenses.append(expense)

    if not matching_expenses:
        print("No expenses found for that date.")
        return

    print_expense_list(matching_expenses, f"Expenses on {date}")


def show_monthly_summary():
    month_text = input("Enter month to summarize (YYYY-MM): ").strip()

    try:
        month = datetime.strptime(month_text, "%Y-%m")
    except ValueError:
        print("Month must be in YYYY-MM format.")
        return

    expenses = get_all_expenses()
    monthly_expenses = []

    for expense in expenses:
        expense_date = parse_date(expense["date"])
        if expense_date.year == month.year and expense_date.month == month.month:
            monthly_expenses.append(expense)

    if not monthly_expenses:
        print("No expenses found for that month.")
        return

    total = sum(expense["amount"] for expense in monthly_expenses)
    print_expense_list(monthly_expenses, f"Expenses for {month_text}")
    print(f"Monthly total: {total:.2f}")


def show_category_totals():
    expenses = get_all_expenses()

    if not expenses:
        print("No expenses found.")
        return

    totals = {}

    for expense in expenses:
        category = expense["category"]
        totals[category] = totals.get(category, 0) + expense["amount"]

    print("\nCategory totals:")
    for category, total in sorted(totals.items()):
        print(f"{category}: {total:.2f}")
