from expense_actions import (
    add_expense,
    delete_expense,
    edit_expense,
    view_expenses,
    view_sorted_expenses,
)
from reports import (
    filter_by_date,
    search_by_category,
    show_category_totals,
    show_monthly_summary,
    show_total,
)
from storage import initialize_database


def main():
    initialize_database()

    while True:
        print("\nExpense Tracker")
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Show Total Spending")
        print("4. Delete Expense")
        print("5. Search by Category")
        print("6. Edit Expense")
        print("7. Filter by Date")
        print("8. Monthly Summary")
        print("9. Category Totals")
        print("10. View Sorted Expenses")
        print("11. Exit")

        choice = input("Enter your choice: ").strip()
        print()

        if choice == "1":
            add_expense()
        elif choice == "2":
            view_expenses()
        elif choice == "3":
            show_total()
        elif choice == "4":
            delete_expense()
        elif choice == "5":
            search_by_category()
        elif choice == "6":
            edit_expense()
        elif choice == "7":
            filter_by_date()
        elif choice == "8":
            show_monthly_summary()
        elif choice == "9":
            show_category_totals()
        elif choice == "10":
            view_sorted_expenses()
        elif choice == "11":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Try again.")
