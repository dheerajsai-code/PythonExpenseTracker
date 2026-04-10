import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "expenses.db")
JSON_FILE_NAME = os.path.join(BASE_DIR, "expenses.json")
SORT_FIELD_MAP = {
    "date": "date",
    "amount": "amount",
    "category": "category",
}


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        # Create users table
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )

        # Create default CLI user if not exists
        connection.execute(
            """
            INSERT OR IGNORE INTO users (id, username, password_hash)
            VALUES (1, 'cli_user', '')
            """
        )

        # Create expenses table if not exists (initially without user_id)
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """
        )

        # Gracefully add user_id column to expenses table if it doesn't exist
        cursor = connection.execute("PRAGMA table_info(expenses)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "user_id" not in columns:
            connection.execute(
                "ALTER TABLE expenses ADD COLUMN user_id INTEGER DEFAULT 1 REFERENCES users(id)"
            )

        # Create budgets table
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, category)
            )
            """
        )

        # Create recurring expenses table
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                frequency TEXT NOT NULL,
                next_due_date TEXT NOT NULL,
                last_processed_date TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )

    migrate_json_data()


def migrate_json_data():
    if not os.path.exists(JSON_FILE_NAME):
        return

    if count_expenses(user_id=1) > 0:
        return

    try:
        with open(JSON_FILE_NAME, "r", encoding="utf-8") as file:
            expenses = json.load(file)
    except (json.JSONDecodeError, OSError):
        print("Could not read expenses.json for migration.")
        return

    if not isinstance(expenses, list):
        print("expenses.json format is invalid. Skipping migration.")
        return

    with get_connection() as connection:
        for expense in expenses:
            connection.execute(
                """
                INSERT INTO expenses (amount, category, date, description, user_id)
                VALUES (?, ?, ?, ?, 1)
                """,
                (
                    expense["amount"],
                    expense["category"],
                    expense["date"],
                    expense["description"],
                ),
            )


def count_expenses(user_id=1):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM expenses WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return row["count"]


def get_all_expenses(user_id=1):
    return get_sorted_expenses("date", user_id=user_id)


def get_expense_by_id(expense_id, user_id=1):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, amount, category, date, description, user_id
            FROM expenses
            WHERE id = ? AND user_id = ?
            """,
            (expense_id, user_id),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def get_sorted_expenses(sort_by="date", descending=False, user_id=1):
    sort_column = SORT_FIELD_MAP.get(sort_by)

    if sort_column is None:
        raise ValueError("Invalid sort field.")

    sort_direction = "DESC" if descending else "ASC"

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, amount, category, date, description, user_id
            FROM expenses
            WHERE user_id = ?
            ORDER BY {sort_column} {sort_direction}, id ASC
            """,
            (user_id,),
        ).fetchall()

    return [dict(row) for row in rows]


def add_expense(amount, category, date, description, user_id=1):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO expenses (amount, category, date, description, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (amount, category, date, description, user_id),
        )


def delete_expense(expense_id, user_id=1):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM expenses WHERE id = ? AND user_id = ?",
            (expense_id, user_id),
        )


def update_expense(expense_id, amount, category, date, description, user_id=1):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE expenses
            SET amount = ?, category = ?, date = ?, description = ?
            WHERE id = ? AND user_id = ?
            """,
            (amount, category, date, description, expense_id, user_id),
        )


# User Management Functions
def create_user(username, password_hash):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
            """,
            (username, password_hash),
        )
        return cursor.lastrowid


def get_user_by_username(username):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def get_user_by_id(user_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, username, password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


# Budget Management Functions
def get_all_budgets(user_id):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, user_id, category, amount FROM budgets WHERE user_id = ? ORDER BY category ASC",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_budget_by_category(user_id, category):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, user_id, category, amount FROM budgets WHERE user_id = ? AND category = ?",
            (user_id, category),
        ).fetchone()
    if row is None:
        return None
    return dict(row)


def set_budget(user_id, category, amount):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO budgets (user_id, category, amount)
            VALUES (?, ?, ?)
            """,
            (user_id, category, amount),
        )


def delete_budget(user_id, budget_id):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM budgets WHERE id = ? AND user_id = ?",
            (budget_id, user_id),
        )


# Recurring Expenses Functions
def get_all_recurring_expenses(user_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, user_id, amount, category, description, frequency, next_due_date, last_processed_date
            FROM recurring_expenses
            WHERE user_id = ?
            ORDER BY next_due_date ASC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_recurring_expense(user_id, amount, category, description, frequency, next_due_date):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO recurring_expenses (user_id, amount, category, description, frequency, next_due_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, amount, category, description, frequency, next_due_date),
        )


def delete_recurring_expense(user_id, recurring_id):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM recurring_expenses WHERE id = ? AND user_id = ?",
            (recurring_id, user_id),
        )


def update_recurring_expense_date(recurring_id, next_due_date, last_processed_date):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE recurring_expenses
            SET next_due_date = ?, last_processed_date = ?
            WHERE id = ?
            """,
            (next_due_date, last_processed_date, recurring_id),
        )

