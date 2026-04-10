from datetime import datetime

import pytest

from validators import get_valid_amount, get_valid_date, parse_date


def test_parse_date_returns_datetime():
    parsed_date = parse_date("2026-04-18")

    assert parsed_date == datetime(2026, 4, 18)


def test_get_valid_amount_returns_float_for_valid_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "250.50")

    result = get_valid_amount("Enter amount: ")

    assert result == 250.50


def test_get_valid_amount_rejects_non_numeric_input(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "abc")

    result = get_valid_amount("Enter amount: ")

    captured = capsys.readouterr()
    assert result is None
    assert "Amount must be a number." in captured.out


def test_get_valid_amount_rejects_non_positive_input(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "0")

    result = get_valid_amount("Enter amount: ")

    captured = capsys.readouterr()
    assert result is None
    assert "Amount must be greater than 0." in captured.out


def test_get_valid_date_accepts_correct_format(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "2026-04-18")

    result = get_valid_date("Enter date: ")

    assert result == "2026-04-18"


def test_get_valid_date_rejects_empty_input(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "   ")

    result = get_valid_date("Enter date: ")

    captured = capsys.readouterr()
    assert result is None
    assert "Date cannot be empty." in captured.out


def test_get_valid_date_rejects_wrong_format(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _: "18/04/2026")

    result = get_valid_date("Enter date: ")

    captured = capsys.readouterr()
    assert result is None
    assert "Date must be in YYYY-MM-DD format." in captured.out


def test_parse_date_raises_for_invalid_date():
    with pytest.raises(ValueError):
        parse_date("2026-02-31")
