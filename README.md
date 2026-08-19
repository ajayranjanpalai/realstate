# 🏠 Real Estate Management System

A full-stack property management application built with Python (Backend) and HTML5/CSS3/JavaScript (Frontend). Features user authentication, property filtering, booking workflows, and automated market analysis charts. Supports PostgreSQL/Neon DB, MySQL, and local SQLite database backends.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup (Optional)
Copy `.env.example` to `.env` to configure your custom database credentials securely:
```bash
cp .env.example .env
```
*(If no database environment variables are set, the system automatically falls back to a zero-config local SQLite database)*

### 3. Run the Application
```bash
python start.py
```
Open your browser at **[http://127.0.0.1:8000](http://127.0.0.1:8000)** or **[http://localhost:8000](http://localhost:8000)**.

---

## 🔒 Security Best Practices
- Never commit `.env` files or database credentials to version control.
- Hardcoded secrets and personal credentials have been removed. Configure custom environment variables via `.env` or host settings.
