import reports


def test_show_total_prints_sum(monkeypatch, capsys):
    monkeypatch.setattr(
        reports,
        "get_all_expenses",
        lambda: [
            {"amount": 100.0, "category": "Food", "date": "2026-04-14", "description": "Lunch"},
            {"amount": 250.0, "category": "Bills", "date": "2026-04-15", "description": "WiFi"},
        ],
    )

    reports.show_total()

    captured = capsys.readouterr()
    assert "Total spending: 350.00" in captured.out


def test_search_by_category_sends_matching_expenses_to_display(monkeypatch):
    captured = {}

    monkeypatch.setattr("builtins.input", lambda _: "food")
    monkeypatch.setattr(
        reports,
        "get_all_expenses",
        lambda: [
            {"amount": 100.0, "category": "Food", "date": "2026-04-14", "description": "Lunch"},
            {"amount": 50.0, "category": "Travel", "date": "2026-04-14", "description": "Bus"},
        ],
    )
    monkeypatch.setattr(
        reports,
        "print_expense_list",
        lambda expenses, heading: captured.update(
            {"expenses": expenses, "heading": heading}
        ),
    )

    reports.search_by_category()

    assert captured["heading"] == "Expenses in category: food"
    assert len(captured["expenses"]) == 1
    assert captured["expenses"][0]["category"] == "Food"


def test_show_monthly_summary_prints_filtered_total(monkeypatch, capsys):
    captured = {}

    monkeypatch.setattr("builtins.input", lambda _: "2026-04")
    monkeypatch.setattr(
        reports,
        "get_all_expenses",
        lambda: [
            {"amount": 100.0, "category": "Food", "date": "2026-04-14", "description": "Lunch"},
            {"amount": 250.0, "category": "Bills", "date": "2026-04-15", "description": "WiFi"},
            {"amount": 90.0, "category": "Travel", "date": "2026-05-01", "description": "Cab"},
        ],
    )
    monkeypatch.setattr(
        reports,
        "print_expense_list",
        lambda expenses, heading: captured.update(
            {"expenses": expenses, "heading": heading}
        ),
    )

    reports.show_monthly_summary()

    output = capsys.readouterr().out
    assert captured["heading"] == "Expenses for 2026-04"
    assert len(captured["expenses"]) == 2
    assert "Monthly total: 350.00" in output


def test_show_category_totals_groups_and_sorts_output(monkeypatch, capsys):
    monkeypatch.setattr(
        reports,
        "get_all_expenses",
        lambda: [
            {"amount": 150.0, "category": "Travel", "date": "2026-04-14", "description": "Bus"},
            {"amount": 100.0, "category": "Food", "date": "2026-04-14", "description": "Lunch"},
            {"amount": 50.0, "category": "Food", "date": "2026-04-15", "description": "Snacks"},
        ],
    )

    reports.show_category_totals()

    output = capsys.readouterr().out
    assert "Category totals:" in output
    assert "Food: 150.00" in output
    assert "Travel: 150.00" in output
