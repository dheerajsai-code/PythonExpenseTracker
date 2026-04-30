import csv
from functools import wraps
from io import StringIO
import os

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for

from storage import (
    add_expense,
    add_recurring_expense,
    create_user,
    delete_budget,
    delete_expense,
    delete_recurring_expense,
    get_all_budgets,
    get_all_recurring_expenses,
    get_expense_by_id,
    get_sorted_expenses,
    get_user_by_username,
    initialize_database,
    set_budget,
    update_expense,
    update_recurring_expense_date,
)
from validators import parse_date


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
initialize_database()

SORT_FIELDS = {"date", "amount", "category"}
SORT_ORDERS = {"asc", "desc"}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def process_due_recurring_expenses(user_id):
    from datetime import datetime, timedelta
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    
    processed_count = 0
    recurring_list = get_all_recurring_expenses(user_id)
    
    for item in recurring_list:
        next_due = item["next_due_date"]
        rec_id = item["id"]
        frequency = item["frequency"].lower()
        
        while next_due <= current_date_str:
            desc = f"[Recurring] {item['description']}"
            add_expense(
                amount=item["amount"],
                category=item["category"],
                date=next_due,
                description=desc,
                user_id=user_id
            )
            
            try:
                due_dt = datetime.strptime(next_due, "%Y-%m-%d")
                if frequency == "daily":
                    next_dt = due_dt + timedelta(days=1)
                elif frequency == "weekly":
                    next_dt = due_dt + timedelta(weeks=1)
                elif frequency == "monthly":
                    year = due_dt.year + (due_dt.month // 12)
                    month = (due_dt.month % 12) + 1
                    try:
                        next_dt = datetime(year, month, due_dt.day)
                    except ValueError:
                        for d in [30, 29, 28]:
                            try:
                                next_dt = datetime(year, month, d)
                                break
                            except ValueError:
                                continue
                elif frequency == "yearly":
                    try:
                        next_dt = datetime(due_dt.year + 1, due_dt.month, due_dt.day)
                    except ValueError:
                        next_dt = datetime(due_dt.year + 1, due_dt.month, 28)
                else:
                    next_dt = due_dt + timedelta(days=30)
                
                next_due = next_dt.strftime("%Y-%m-%d")
            except Exception:
                next_due = (datetime.strptime(next_due, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
            
            update_recurring_expense_date(
                recurring_id=rec_id,
                next_due_date=next_due,
                last_processed_date=current_date_str
            )
            processed_count += 1
            
    if processed_count > 0:
        flash(f"Processed {processed_count} recurring expense(s) that were due.", "success")


def validate_web_expense_form(form_data):
    errors = []

    amount_text = form_data.get("amount", "").strip()
    category = form_data.get("category", "").strip()
    date = form_data.get("date", "").strip()
    description = form_data.get("description", "").strip()

    try:
        amount = float(amount_text)
    except ValueError:
        errors.append("Amount must be a number.")
        amount = None
    else:
        if amount <= 0:
            errors.append("Amount must be greater than 0.")

    if not category:
        errors.append("Category cannot be empty.")

    if not date:
        errors.append("Date cannot be empty.")
    else:
        try:
            parse_date(date)
        except ValueError:
            errors.append("Date must be in YYYY-MM-DD format.")

    if not description:
        errors.append("Description cannot be empty.")

    return errors, amount, category, date, description


# Authentication Routes
from werkzeug.security import check_password_hash, generate_password_hash


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
        
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        errors = []
        if not username:
            errors.append("Username cannot be empty.")
        if not password:
            errors.append("Password cannot be empty.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
            
        if not errors:
            existing = get_user_by_username(username)
            if existing:
                errors.append("Username already exists.")
                
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("register.html", form_data=request.form)
            
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        user_id = create_user(username, hashed_password)
        session["user_id"] = user_id
        session["username"] = username
        flash("Registration successful! Welcome.", "success")
        return redirect(url_for("index"))
        
    return render_template("register.html", form_data={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
        
    next_url = request.args.get("next") or request.form.get("next")
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        user = get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Logged in successfully.", "success")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("index"))
            
        flash("Invalid username or password.", "error")
        return render_template("login.html", username=username, next=next_url)
        
    return render_template("login.html", next=next_url)


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# Core Application Routes
@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    process_due_recurring_expenses(user_id)
    
    sort_by = request.args.get("sort_by", "date").lower()
    order = request.args.get("order", "asc").lower()

    if sort_by not in SORT_FIELDS:
        sort_by = "date"

    if order not in SORT_ORDERS:
        order = "asc"

    expenses = get_sorted_expenses(sort_by, descending=(order == "desc"), user_id=user_id)
    total_spending = sum(expense["amount"] for expense in expenses)

    # Category breakdown aggregates
    category_totals = {}
    for expense in expenses:
        cat = expense["category"]
        category_totals[cat] = category_totals.get(cat, 0.0) + expense["amount"]

    # Monthly trends aggregates (last 6 months)
    monthly_totals = {}
    for expense in expenses:
        try:
            ym = expense["date"][:7]  # YYYY-MM
            monthly_totals[ym] = monthly_totals.get(ym, 0.0) + expense["amount"]
        except Exception:
            pass

    sorted_months = sorted(monthly_totals.keys())[-6:]
    monthly_labels = sorted_months
    monthly_values = [monthly_totals[m] for m in sorted_months]

    # Budgets tracking
    budgets_list = get_all_budgets(user_id)
    budgets_data = []
    
    from datetime import datetime
    current_month_prefix = datetime.now().strftime("%Y-%m")
    
    current_month_spending = {}
    for expense in expenses:
        if expense["date"].startswith(current_month_prefix):
            cat = expense["category"]
            current_month_spending[cat] = current_month_spending.get(cat, 0.0) + expense["amount"]

    for b in budgets_list:
        cat = b["category"]
        spent = current_month_spending.get(cat, 0.0)
        limit = b["amount"]
        pct = (spent / limit) * 100 if limit > 0 else 0.0
        budgets_data.append({
            "id": b["id"],
            "category": cat,
            "limit": limit,
            "spent": spent,
            "percentage": min(pct, 100.0),
            "raw_percentage": pct
        })

    return render_template(
        "index.html",
        expenses=expenses,
        total_spending=total_spending,
        sort_by=sort_by,
        order=order,
        category_labels=list(category_totals.keys()),
        category_values=list(category_totals.values()),
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
        budgets=budgets_data,
    )


@app.route("/expenses/new", methods=["GET", "POST"])
@login_required
def create_expense():
    user_id = session["user_id"]
    if request.method == "POST":
        errors, amount, category, date, description = validate_web_expense_form(
            request.form
        )

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_expense.html", form_data=request.form)

        add_expense(amount, category, date, description, user_id=user_id)
        flash("Expense added successfully.", "success")
        return redirect(url_for("index"))

    return render_template("add_expense.html", form_data={})


@app.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    user_id = session["user_id"]
    expense = get_expense_by_id(expense_id, user_id=user_id)

    if expense is None:
        flash("Expense not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        errors, amount, category, date, description = validate_web_expense_form(
            request.form
        )

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "edit_expense.html",
                expense=expense,
                form_data=request.form,
            )

        update_expense(expense_id, amount, category, date, description, user_id=user_id)
        flash("Expense updated successfully.", "success")
        return redirect(url_for("index"))

    return render_template("edit_expense.html", expense=expense, form_data=expense)


@app.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def remove_expense(expense_id):
    user_id = session["user_id"]
    # Check ownership
    expense = get_expense_by_id(expense_id, user_id=user_id)
    if expense is None:
        flash("Expense not found or unauthorized.", "error")
    else:
        delete_expense(expense_id, user_id=user_id)
        flash("Expense deleted successfully.", "success")
    return redirect(url_for("index"))


# Budget Management Routes
@app.route("/budgets", methods=["GET", "POST"])
@login_required
def manage_budgets():
    user_id = session["user_id"]
    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_text = request.form.get("amount", "").strip()

        errors = []
        if not category:
            errors.append("Category cannot be empty.")
        try:
            amount = float(amount_text)
            if amount <= 0:
                errors.append("Budget amount must be greater than 0.")
        except ValueError:
            errors.append("Budget amount must be a number.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            set_budget(user_id, category, amount)
            flash(f"Budget for '{category}' updated.", "success")
            return redirect(url_for("manage_budgets"))

    budgets = get_all_budgets(user_id)
    return render_template("budgets.html", budgets=budgets)


@app.route("/budgets/<int:budget_id>/delete", methods=["POST"])
@login_required
def remove_budget(budget_id):
    user_id = session["user_id"]
    delete_budget(user_id, budget_id)
    flash("Budget deleted successfully.", "success")
    return redirect(url_for("manage_budgets"))


# Recurring Expenses Routes
@app.route("/recurring", methods=["GET", "POST"])
@login_required
def manage_recurring():
    user_id = session["user_id"]
    
    if request.method == "POST":
        amount_text = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        frequency = request.form.get("frequency", "").strip().lower()
        start_date = request.form.get("start_date", "").strip()

        errors = []
        try:
            amount = float(amount_text)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a number.")

        if not category:
            errors.append("Category cannot be empty.")
        if not description:
            errors.append("Description cannot be empty.")
        if frequency not in {"daily", "weekly", "monthly", "yearly"}:
            errors.append("Frequency must be Daily, Weekly, Monthly, or Yearly.")
        if not start_date:
            errors.append("Start Date cannot be empty.")
        else:
            try:
                parse_date(start_date)
            except ValueError:
                errors.append("Start Date must be in YYYY-MM-DD format.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "recurring.html",
                recurring_expenses=get_all_recurring_expenses(user_id),
                form_data=request.form,
            )

        add_recurring_expense(user_id, amount, category, description, frequency, start_date)
        flash("Recurring expense schedule created successfully.", "success")
        return redirect(url_for("manage_recurring"))

    recurring_expenses = get_all_recurring_expenses(user_id)
    return render_template("recurring.html", recurring_expenses=recurring_expenses, form_data={})


@app.route("/recurring/<int:recurring_id>/delete", methods=["POST"])
@login_required
def remove_recurring(recurring_id):
    user_id = session["user_id"]
    delete_recurring_expense(user_id, recurring_id)
    flash("Recurring expense schedule deleted successfully.", "success")
    return redirect(url_for("manage_recurring"))


# CSV Export Route
@app.route("/expenses/export/csv")
@login_required
def export_csv():
    user_id = session["user_id"]
    expenses = get_sorted_expenses("date", descending=False, user_id=user_id)

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Date", "Category", "Amount", "Description"])
    for exp in expenses:
        cw.writerow([exp["id"], exp["date"], exp["category"], exp["amount"], exp["description"]])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=expenses_export.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True)

