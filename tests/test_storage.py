import json

import storage


def test_initialize_database_migrates_json_data(tmp_path, monkeypatch):
    test_db = tmp_path / "expenses.db"
    test_json = tmp_path / "expenses.json"
    sample_expenses = [
        {
            "amount": 100.0,
            "category": "Food",
            "date": "2026-04-14",
            "description": "Lunch",
        },
        {
            "amount": 200.0,
            "category": "Travel",
            "date": "2026-04-15",
            "description": "Bus pass",
        },
    ]
    test_json.write_text(json.dumps(sample_expenses), encoding="utf-8")

    monkeypatch.setattr(storage, "DB_NAME", str(test_db))
    monkeypatch.setattr(storage, "JSON_FILE_NAME", str(test_json))

    storage.initialize_database()

    expenses = storage.get_all_expenses()
    assert len(expenses) == 2
    assert expenses[0]["category"] == "Food"
    assert expenses[1]["category"] == "Travel"


def test_add_update_and_delete_expense(tmp_path, monkeypatch):
    test_db = tmp_path / "expenses.db"
    test_json = tmp_path / "expenses.json"

    monkeypatch.setattr(storage, "DB_NAME", str(test_db))
    monkeypatch.setattr(storage, "JSON_FILE_NAME", str(test_json))

    storage.initialize_database()

    storage.add_expense(75.0, "Travel", "2026-04-26", "Metro card")
    expenses = storage.get_all_expenses()

    assert len(expenses) == 1
    assert expenses[0]["description"] == "Metro card"

    expense_id = expenses[0]["id"]
    storage.update_expense(
        expense_id,
        95.0,
        "Travel",
        "2026-04-26",
        "Metro recharge",
    )

    updated_expenses = storage.get_all_expenses()
    assert updated_expenses[0]["amount"] == 95.0
    assert updated_expenses[0]["description"] == "Metro recharge"

    storage.delete_expense(expense_id)
    final_expenses = storage.get_all_expenses()
    assert final_expenses == []


def test_get_sorted_expenses_sorts_by_amount_and_category(tmp_path, monkeypatch):
    test_db = tmp_path / "expenses.db"
    test_json = tmp_path / "expenses.json"

    monkeypatch.setattr(storage, "DB_NAME", str(test_db))
    monkeypatch.setattr(storage, "JSON_FILE_NAME", str(test_json))

    storage.initialize_database()
    storage.add_expense(300.0, "Study", "2026-04-18", "Workbook")
    storage.add_expense(150.0, "Food", "2026-04-14", "Lunch")
    storage.add_expense(500.0, "Bills", "2026-04-16", "Internet")

    by_amount_desc = storage.get_sorted_expenses("amount", descending=True)
    assert [expense["amount"] for expense in by_amount_desc] == [500.0, 300.0, 150.0]

    by_category_asc = storage.get_sorted_expenses("category")
    assert [expense["category"] for expense in by_category_asc] == [
        "Bills",
        "Food",
        "Study",
    ]
