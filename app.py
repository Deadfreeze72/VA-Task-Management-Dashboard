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
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import csv
import io


app = Flask(__name__)

app.config["SECRET_KEY"] = "caesar_dashboard_secret_key"


basedir = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + os.path.join(basedir, "tasks.db")
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"



# =========================
# DATABASE MODELS
# =========================


class User(db.Model, UserMixin):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )


    tasks = db.relationship(
        "Task",
        backref="owner",
        lazy=True
    )



class Task(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )


    title = db.Column(
        db.String(200),
        nullable=False
    )


    priority = db.Column(
        db.String(50),
        default="Medium"
    )


    status = db.Column(
        db.String(50),
        default="Pending"
    )


    due_date = db.Column(
        db.String(50)
    )


    created = db.Column(
        db.String(50),
        default=lambda:
        datetime.now().strftime("%Y-%m-%d")
    )


    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )



@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# =========================
# REGISTER
# =========================


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"].lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]


        existing_user = User.query.filter_by(
            email=email
        ).first()


        if existing_user:

            flash(
                "This email already has an account. Please login.",
                "danger"
            )

            return redirect("/register")



        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect("/register")



        user = User(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )


        db.session.add(user)
        db.session.commit()


        flash(
            "Account created successfully.",
            "success"
        )


        return redirect("/login")



    return render_template("register.html")





# =========================
# LOGIN
# =========================


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].lower()
        password = request.form["password"]


        user = User.query.filter_by(
            email=email
        ).first()



        if user is None:

            flash(
                "No account found. Please register first.",
                "danger"
            )

            return redirect("/login")



        if not check_password_hash(
            user.password,
            password
        ):

            flash(
                "Incorrect password.",
                "danger"
            )

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


    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()



    total = len(tasks)



    completed = len(
        [
            task for task in tasks
            if task.status == "Completed"
        ]
    )


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


    title = request.form["title"]

    priority = request.form["priority"]

    days_input = request.form["days"]



    try:

        days = int(days_input)


    except ValueError:

        flash(
            "Please enter a valid number of days.",
            "danger"
        )

        return redirect("/")



    if days < 1 or days > 90:

        flash(
            "Due date must be between 1 and 90 days.",
            "danger"
        )

        return redirect("/")



    due = (
        datetime.today()
        +
        timedelta(days=days)
    ).strftime("%Y-%m-%d")



    task = Task(
        title=title,
        priority=priority,
        due_date=due,
        user_id=current_user.id
    )


    db.session.add(task)

    db.session.commit()



    flash(
        "Task added successfully.",
        "success"
    )


    return redirect("/")





# =========================
# EDIT TASK
# =========================


@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):


    task = Task.query.get_or_404(id)



    if task.user_id != current_user.id:

        return redirect("/")



    if request.method == "POST":


        task.title = request.form["title"]

        task.priority = request.form["priority"]

        days = int(request.form["days"])



        task.due_date = (
            datetime.today()
            +
            timedelta(days=days)
        ).strftime("%Y-%m-%d")



        db.session.commit()



        flash(
            "Task updated successfully.",
            "success"
        )


        return redirect("/")



    return render_template(
        "edit_task.html",
        task=task
    )





# =========================
# COMPLETE TASK
# =========================


@app.route("/complete/<int:id>")
@login_required
def complete(id):


    task = Task.query.get_or_404(id)



    if task.user_id == current_user.id:

        task.status = "Completed"

        db.session.commit()



    return redirect("/")





# =========================
# DELETE TASK
# =========================


@app.route("/delete/<int:id>")
@login_required
def delete(id):


    task = Task.query.get_or_404(id)



    if task.user_id == current_user.id:

        db.session.delete(task)

        db.session.commit()



    return redirect("/")


# =========================
# STATISTICS
# =========================


@app.route("/stats")
@login_required
def stats():


    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()



    completed = len(
        [
            task for task in tasks
            if task.status == "Completed"
        ]
    )



    pending = len(tasks) - completed



    high = len(
        [
            task for task in tasks
            if task.priority == "High"
        ]
    )



    medium = len(
        [
            task for task in tasks
            if task.priority == "Medium"
        ]
    )



    low = len(
        [
            task for task in tasks
            if task.priority == "Low"
        ]
    )



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


    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).all()



    output = io.StringIO()


    writer = csv.writer(output)



    writer.writerow(
        [
            "Task",
            "Priority",
            "Status",
            "Due Date",
            "Created Date"
        ]
    )



    for task in tasks:

        writer.writerow(
            [
                task.title,
                task.priority,
                task.status,
                task.due_date,
                task.created
            ]
        )



    output.seek(0)



    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=my_tasks.csv"
        }
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

    app.run(debug=True)