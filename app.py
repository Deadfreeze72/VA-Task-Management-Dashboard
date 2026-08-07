from flask import Flask, render_template, request, redirect, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import csv
import io

app = Flask(__name__)

# SECRET_KEY now comes from the environment instead of being hardcoded.
# Locally, set it via a .env file (see .env.example) or an env var.
# In production (Render, etc.) set SECRET_KEY in the dashboard's
# environment settings. Falls back to a random key so the app never
# silently runs with a known/leaked secret.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32).hex()

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    os.environ.get("DATABASE_URL")
    or "sqlite:///" + os.path.join(basedir, "tasks.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# CSRF protection for every POST form in the app.
csrf = CSRFProtect(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

VALID_PRIORITIES = {"High", "Medium", "Low"}

# =========================
# DATABASE MODELS
# =========================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship("Task", backref="owner", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    priority = db.Column(db.String(50), default="Medium")
    status = db.Column(db.String(50), default="Pending")
    due_date = db.Column(db.String(50))
    created = db.Column(
        db.String(50),
        default=lambda: datetime.now().strftime("%Y-%m-%d")
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect("/register")

        # Basic email sanity check (not exhaustive, but catches obvious typos)
        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "danger")
            return redirect("/register")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return redirect("/register")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("This email already has an account. Please login.", "danger")
            return redirect("/register")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect("/register")

        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully.", "success")
        return redirect("/login")

    return render_template("register.html")


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # Same generic message whether the email doesn't exist or the
        # password is wrong -- avoids confirming which emails are registered.
        if user is None or not check_password_hash(user.password, password):
            flash("Invalid email or password.", "danger")
            return redirect("/login")

        login_user(user)
        return redirect("/")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


# =========================
# DASHBOARD
# =========================
@app.route("/")
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    total = len(tasks)
    completed = len([task for task in tasks if task.status == "Completed"])
    pending = total - completed

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending
    )


# =========================
# ADD TASK
# =========================
@app.route("/add", methods=["POST"])
@login_required
def add_task():
    title = request.form.get("title", "").strip()
    priority = request.form.get("priority", "Medium")
    days_input = request.form.get("days", "")

    if not title:
        flash("Task title cannot be empty.", "danger")
        return redirect("/")

    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    try:
        days = int(days_input)
    except ValueError:
        flash("Please enter a valid number of days.", "danger")
        return redirect("/")

    if days < 1 or days > 90:
        flash("Due date must be between 1 and 90 days.", "danger")
        return redirect("/")

    due = (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d")

    task = Task(
        title=title,
        priority=priority,
        due_date=due,
        user_id=current_user.id
    )
    db.session.add(task)
    db.session.commit()

    flash("Task added successfully.", "success")
    return redirect("/")


# =========================
# EDIT TASK
# =========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        flash("You don't have permission to edit that task.", "danger")
        return redirect("/")

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        priority = request.form.get("priority", "Medium")
        days_input = request.form.get("days", "")

        if not title:
            flash("Task title cannot be empty.", "danger")
            return redirect(f"/edit/{id}")

        if priority not in VALID_PRIORITIES:
            priority = "Medium"

        try:
            days = int(days_input)
        except ValueError:
            flash("Please enter a valid number of days.", "danger")
            return redirect(f"/edit/{id}")

        if days < 1 or days > 90:
            flash("Due date must be between 1 and 90 days.", "danger")
            return redirect(f"/edit/{id}")

        task.title = title
        task.priority = priority
        task.due_date = (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d")
        db.session.commit()

        flash("Task updated successfully.", "success")
        return redirect("/")

    return render_template("edit_task.html", task=task)


# =========================
# COMPLETE TASK
# (POST now, was GET -- state changes should never happen via a plain link)
# =========================
@app.route("/complete/<int:id>", methods=["POST"])
@login_required
def complete(id):
    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        flash("You don't have permission to update that task.", "danger")
        return redirect("/")

    task.status = "Completed"
    db.session.commit()
    flash("Task marked as completed.", "success")
    return redirect("/")


# =========================
# DELETE TASK
# (POST now, was GET)
# =========================
@app.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        flash("You don't have permission to delete that task.", "danger")
        return redirect("/")

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "success")
    return redirect("/")


# =========================
# STATISTICS
# =========================
@app.route("/stats")
@login_required
def stats():
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    completed = len([task for task in tasks if task.status == "Completed"])
    pending = len(tasks) - completed
    high = len([task for task in tasks if task.priority == "High"])
    medium = len([task for task in tasks if task.priority == "Medium"])
    low = len([task for task in tasks if task.priority == "Low"])

    return render_template(
        "stats.html",
        completed=completed,
        pending=pending,
        high=high,
        medium=medium,
        low=low
    )


# =========================
# EXPORT CSV
# =========================
@app.route("/export")
@login_required
def export():
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Task", "Priority", "Status", "Due Date", "Created Date"])

    for task in tasks:
        writer.writerow([task.title, task.priority, task.status, task.due_date, task.created])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=my_tasks.csv"}
    )


# =========================
# CREATE DATABASE
# =========================
with app.app_context():
    db.create_all()


# =========================
# START APPLICATION
# =========================
if __name__ == "__main__":
    # debug mode now driven by an env var so it can never accidentally
    # ship "on" in production. Locally: set FLASK_DEBUG=1
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)
