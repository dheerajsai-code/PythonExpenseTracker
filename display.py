def get_expense_column_widths(expenses):
    amount_width = max(len(f"{expense['amount']:.2f}") for expense in expenses)
    category_width = max(len(expense["category"]) for expense in expenses)
    date_width = max(len(expense["date"]) for expense in expenses)
    description_width = max(len(expense["description"]) for expense in expenses)
    index_width = max(len(str(len(expenses))), len("No"))

    return {
        "index": index_width,
        "amount": amount_width,
        "category": category_width,
        "date": date_width,
        "description": description_width,
    }


def format_expense_line(index, expense, widths):
    return (
        f"{index:<{widths['index']}} | "
        f"{expense['amount']:<{widths['amount']}.2f} | "
        f"{expense['category']:<{widths['category']}} | "
        f"{expense['date']:<{widths['date']}} | "
        f"{expense['description']:<{widths['description']}}"
    )


def print_expense_list(expenses, heading="All Expenses"):
    if not expenses:
        print("No expenses found.")
        return

    widths = get_expense_column_widths(expenses)
    header = (
        f"{'No':<{widths['index']}} | "
        f"{'Amount':<{widths['amount']}} | "
        f"{'Category':<{widths['category']}} | "
        f"{'Date':<{widths['date']}} | "
        f"{'Description':<{widths['description']}}"
    )
    divider = "-" * len(header)

    print(f"\n{heading}:")
    print(header)
    print(divider)
    for index, expense in enumerate(expenses, start=1):
        print(format_expense_line(index, expense, widths))
