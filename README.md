# Job Application Tracker

A full-stack web app to track job applications — built with **pure Python** (no frameworks), MySQL, HTML, CSS, and JavaScript during my internship at Wish 2 Skill LLP (Jan–Apr 2026).

## Features

- Add, edit, and delete job applications
- Filter by status (Applied / Interview / Offer / Rejected) or search by company/role
- Dashboard with summary stats
- Clean responsive UI
- Built using Python's built-in `http.server` — no Flask, no Django

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Python (`http.server`, `urllib`)    |
| Database   | MySQL (`mysql-connector-python`)    |
| Frontend   | HTML, CSS, JavaScript (vanilla)     |

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/vardhanshetty06/job-tracker.git
cd job-tracker
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

```bash
mysql -u root -p < database/schema.sql
```

### 5. Configure environment variables

```bash
cp .env.example .env
# then edit .env and fill in your MySQL credentials
```

### 6. Run the app

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Project Structure

```
job-tracker/
├── app.py                  # HTTP server + routing + DB logic
├── requirements.txt
├── .env.example
├── .gitignore
├── database/
│   └── schema.sql
├── templates/
│   └── base.html
└── static/
    ├── css/style.css
    └── js/main.js
```

## What I Learned

- Building an HTTP server from scratch using Python's standard library
- Parsing GET/POST requests and query strings manually
- Connecting Python to MySQL using `mysql-connector-python`
- Writing parameterized SQL queries to prevent injection
- End-to-end CRUD web app without any web framework

---

Built as part of my internship at **Wish 2 Skill LLP** (Jan–Apr 2026).
