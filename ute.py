import sqlite3
from datetime import datetime

DB = "ute.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Users: Added National ID and Admin Approval logic
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT UNIQUE, 
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        national_id TEXT UNIQUE,
        password TEXT, 
        role TEXT, 
        is_approved_admin INTEGER DEFAULT 0,
        admin_request_pending INTEGER DEFAULT 0
    )""")
    # Contracts: The 12-month timer
    c.execute("""CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY, 
        employer TEXT, 
        employee TEXT, 
        total_months_paid INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active'
    )""")
    # Ledger: 30%/10% Math + AI Fraud Score
    c.execute("""CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY, 
        contract_id INTEGER,
        gross_paid REAL,
        ute_retention REAL,
        employer_cashback REAL,
        employee_net REAL,
        fraud_score REAL DEFAULT 0.0,
        timestamp DATETIME
    )""")
    c.execute("CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY, username TEXT UNIQUE, balance REAL DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, employer TEXT, title TEXT, description TEXT, requirements TEXT, location TEXT, salary REAL)")
    conn.commit()
    conn.close()

def get_balance(user):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT balance FROM wallet WHERE username=?", (user,)).fetchone()
    conn.close()
    return row[0] if row else 0

def calculate_split(salary, months_paid):
    """30% Month 1, 10% Months 2-12. Plus 3% fee."""
    fee = salary * 0.03
    if months_paid == 0:
        return {"total": salary + fee, "ute": salary * 0.20, "cash": salary * 0.10, "net": salary * 0.70}
    return {"total": salary + fee, "ute": salary * 0.06, "cash": salary * 0.04, "net": salary * 0.90}
