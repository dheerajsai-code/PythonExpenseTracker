from display import print_expense_list
from storage import (
    add_expense as add_expense_to_db,
    delete_expense as delete_expense_from_db,
    get_all_expenses,
    get_sorted_expenses,
    update_expense,
)
from validators import get_valid_amount, get_valid_date, parse_date


def add_expense():
    amount = get_valid_amount("Enter amount: ")
    if amount is None:
        return

    category = input("Enter category: ").strip()
    if not category:
        print("Category cannot be empty.")
        return

    date = get_valid_date("Enter date (YYYY-MM-DD): ")
    if date is None:
        return

    description = input("Enter description: ").strip()
    if not description:
        print("Description cannot be empty.")
        return

    add_expense_to_db(amount, category, date, description)
    print("Expense added successfully.")


def view_expenses():
    expenses = get_all_expenses()
    print_expense_list(expenses)


def view_sorted_expenses():
    print("Sort by:")
    print("1. Date")
    print("2. Amount")
    print("3. Category")

    sort_choice = input("Enter your sort choice: ").strip()

    sort_options = {
        "1": "date",
        "2": "amount",
        "3": "category",
    }

    sort_by = sort_options.get(sort_choice)
    if sort_by is None:
        print("Invalid sort choice.")
        return

    order_choice = input("Enter order (asc/desc): ").strip().lower()
    if order_choice not in {"asc", "desc"}:
        print("Invalid order. Use 'asc' or 'desc'.")
        return

    expenses = get_sorted_expenses(sort_by, descending=(order_choice == "desc"))
    heading = f"Expenses sorted by {sort_by} ({order_choice})"
    print_expense_list(expenses, heading)


def delete_expense():
    expenses = get_all_expenses()
    print_expense_list(expenses)

    if not expenses:
        return

    try:
        choice = int(input("Enter expense number to delete: ").strip())
    except ValueError:
        print("Please enter a valid number.")
        return

    if 1 <= choice <= len(expenses):
        selected_expense = expenses[choice - 1]
        delete_expense_from_db(selected_expense["id"])
        print(f"Deleted expense: {selected_expense['description']}")
    else:
        print("Invalid expense number.")


def edit_expense():
    expenses = get_all_expenses()
    print_expense_list(expenses)

    if not expenses:
        return

    try:
        choice = int(input("Enter expense number to edit: ").strip())
    except ValueError:
        print("Please enter a valid number.")
        return

    if not 1 <= choice <= len(expenses):
        print("Invalid expense number.")
        return

    expense = expenses[choice - 1]

    new_amount = input(f"Enter new amount [{expense['amount']}]: ").strip()
    new_category = input(f"Enter new category [{expense['category']}]: ").strip()
    new_date = input(f"Enter new date [{expense['date']}]: ").strip()
    new_description = input(
        f"Enter new description [{expense['description']}]: "
    ).strip()

    updated_amount = expense["amount"]
    updated_category = expense["category"]
    updated_date = expense["date"]
    updated_description = expense["description"]

    if new_amount:
        try:
            parsed_amount = float(new_amount)
        except ValueError:
            print("Invalid amount. Keeping old amount.")
        else:
            if parsed_amount > 0:
                updated_amount = parsed_amount
            else:
                print("Amount must be greater than 0. Keeping old amount.")

    if new_category:
        updated_category = new_category

    if new_date:
        try:
            parse_date(new_date)
        except ValueError:
            print("Invalid date. Keeping old date.")
        else:
            updated_date = new_date

    if new_description:
        updated_description = new_description

    update_expense(
        expense["id"],
        updated_amount,
        updated_category,
        updated_date,
        updated_description,
    )
    print("Expense updated successfully.")
