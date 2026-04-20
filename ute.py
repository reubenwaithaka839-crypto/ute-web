import sqlite3
from datetime import datetime

DB = "ute.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # 1. Users Table (Identity, Admin Status, and Bank Details)
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT, 
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        national_id TEXT UNIQUE,
        password TEXT, 
        role TEXT, 
        is_approved_admin INTEGER DEFAULT 0,
        admin_request_pending INTEGER DEFAULT 0,
        bank_account TEXT
    )""")

    # 2. Contracts Table (The 12-Month Loyalty Timer)
    c.execute("""CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY, 
        employer TEXT, 
        employee TEXT, 
        total_months_paid INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        start_date TIMESTAMP
    )""")

    # 3. Financial Ledger (Records 30%/10% splits & AI Fraud Scores)
    c.execute("""CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY, 
        contract_id INTEGER,
        gross_amount REAL,
        ute_share REAL,
        employer_cashback REAL,
        employee_net REAL,
        fraud_score REAL,
        timestamp DATETIME
    )""")

    c.execute("CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY, username TEXT UNIQUE, balance REAL DEFAULT 0)")
    conn.commit()
    conn.close()

def calculate_ute_split(salary, months_paid):
    """
    The UTE Formula:
    Month 1: 30% Total Deduction (20% UTE, 10% Cashback)
    Month 2-12: 10% Total Deduction (6% UTE, 4% Cashback)
    Plus 3% platform transaction fee paid by Employer.
    """
    fee = salary * 0.03
    total_due = salary + fee

    if months_paid == 0:
        return {
            "total": total_due,
            "ute": salary * 0.20,
            "cashback": salary * 0.10,
            "net": salary * 0.70
        }
    else:
        return {
            "total": total_due,
            "ute": salary * 0.06,
            "cashback": salary * 0.04,
            "net": salary * 0.90
        }
