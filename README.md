# VA Task Management Dashboard

[![Live Demo](https://img.shields.io/badge/Live-Demo-success)](https://va-task-management-dashboard.onrender.com/login
)

A professional task management dashboard designed for Virtual Assistants to organize client tasks, track deadlines, monitor productivity, and manage daily workflows efficiently.

Built with Flask, this application demonstrates practical skills in web development, database management, authentication, task automation, and deployment.

## 🚀 Live Demo

https://va-task-management-dashboard.onrender.com/login

## 💡 Why I Built This

As I developed my skills as a Virtual Assistant, I realized that managing tasks, deadlines, and priorities efficiently is critical.

This project was built to simulate a real-world productivity tool that helps organize daily workflows, track performance, and improve efficiency using a clean and simple interface.

## 📌 Features

### 🔐 User Management
- User registration
- Secure login/logout
- Individual user dashboards

### ✅ Task Management
- Create tasks
- Edit tasks
- Delete tasks
- Mark tasks as completed
- Set task priorities
- Automatic due date calculation

### 📊 Dashboard
- Total task overview
- Completed and pending task statistics
- Clean and responsive dashboard interface

### 📈 Analytics
- Task completion charts
- Priority distribution charts
- Productivity tracking

### 📁 Export
- Export tasks into CSV format for reporting and record keeping

## 🔒 Security

[#-security](#-security)

This project follows several security best practices:

- **Environment-based secrets** — the Flask `SECRET_KEY` is loaded from an environment variable rather than hardcoded in source, so it's never exposed in version control.
- **CSRF protection** — every form (login, register, add task, edit task, complete, delete) is protected against cross-site request forgery using Flask-WTF.
- **Password hashing** — user passwords are hashed with Werkzeug's `generate_password_hash` before being stored; plaintext passwords are never saved.
- **State-changing actions require POST** — completing or deleting a task can no longer be triggered by simply visiting a link; both require an authenticated POST request.
- **Ownership checks** — every task action verifies the task belongs to the logged-in user before allowing edits, completion, or deletion.
- **Generic auth error messages** — login failures return a single generic message rather than revealing whether a given email is registered.
- **Debug mode off by default** — the app only runs with Flask's debug mode enabled when explicitly configured via an environment variable, preventing accidental exposure of stack traces in production.

## 🛠️ Technologies Used

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- SQLite Database
- HTML5
- CSS3
- JavaScript
- Chart.js

## 📂 Project Structure
## 📸 Screenshots

### Dashboard

![Dashboard](static/images/dashboard.png)


### Statistics

![Statistics](static/images/statistics.png)


### Login

![Login](static/images/login.png)


## 👨‍💻 Author

**Caesar Weyipe Awariwe**

Virtual Assistant | Data Entry Specialist | Flask Developer