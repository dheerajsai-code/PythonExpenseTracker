import pytest
import storage


def test_user_management(tmp_path, monkeypatch):
    test_db = tmp_path / "expenses.db"
    monkeypatch.setattr(storage, "DB_NAME", str(test_db))

    storage.initialize_database()

    # Test create user
    user_id = storage.create_user("test_user", "hashed_password_123")
    assert user_id > 1

    # Test lookup by username
    user = storage.get_user_by_username("test_user")
    assert user is not None
    assert user["id"] == user_id
    assert user["password_hash"] == "hashed_password_123"

    # Test lookup by ID
    user_by_id = storage.get_user_by_id(user_id)
    assert user_by_id == user

    # Non-existent user
    assert storage.get_user_by_username("non_existent") is None
    assert storage.get_user_by_id(999) is None


def test_budget_management(tmp_path, monkeypatch):
    test_db = tmp_path / "expenses.db"
    monkeypatch.setattr(storage, "DB_NAME", str(test_db))

    storage.initialize_database()

    # Set budgets
    storage.set_budget(user_id=2, category="Food", amount=150.0)
    storage.set_budget(user_id=2, category="Travel", amount=50.0)

    # Get all budgets
    budgets = storage.get_all_budgets(user_id=2)
    assert len(budgets) == 2
    assert budgets[0]["category"] == "Food"
    assert budgets[0]["amount"] == 150.0

    # Update budget
    storage.set_budget(user_id=2, category="Food", amount=200.0)
    budget = storage.get_budget_by_category(user_id=2, category="Food")
    assert budget["amount"] == 200.0

    # Delete budget using updated id
    storage.delete_budget(user_id=2, budget_id=budget["id"])
    assert len(storage.get_all_budgets(user_id=2)) == 1


def test_recurring_expenses(tmp_path, monkeypatch):
    test_db = tmp_path / "expenses.db"
    monkeypatch.setattr(storage, "DB_NAME", str(test_db))

    storage.initialize_database()

    # Add recurring expense
    storage.add_recurring_expense(
        user_id=2,
        amount=10.0,
        category="Subscriptions",
        description="Music",
        frequency="monthly",
        next_due_date="2026-05-01",
    )

    recurring = storage.get_all_recurring_expenses(user_id=2)
    assert len(recurring) == 1
    assert recurring[0]["description"] == "Music"

    # Update date
    storage.update_recurring_expense_date(
        recurring[0]["id"], "2026-06-01", "2026-05-01"
    )
    updated = storage.get_all_recurring_expenses(user_id=2)
    assert updated[0]["next_due_date"] == "2026-06-01"
    assert updated[0]["last_processed_date"] == "2026-05-01"

    # Delete recurring
    storage.delete_recurring_expense(user_id=2, recurring_id=recurring[0]["id"])
    assert len(storage.get_all_recurring_expenses(user_id=2)) == 0
