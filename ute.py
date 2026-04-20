import sqlite3
from datetime import datetime

DB = "ute.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Users: Includes NID, Phone, and Location-based skills
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT, 
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        national_id TEXT UNIQUE,
        password TEXT, 
        role TEXT, 
        location TEXT,
        skills TEXT,
        is_approved_admin INTEGER DEFAULT 0
    )""")
    # Contracts: Tracks the 12-month platform mandate
    c.execute("""CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY, 
        employer TEXT, 
        employee TEXT, 
        salary REAL,
        total_months_paid INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active'
    )""")
    # Ledger: The Audit Trail for your Bank Revenue
    c.execute("""CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY, 
        contract_id INTEGER,
        gross_total REAL,
        ute_share REAL,
        employer_cashback REAL,
        employee_net REAL,
        timestamp DATETIME
    )""")
    c.execute("CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY, username TEXT UNIQUE, balance REAL DEFAULT 0)")
    conn.commit()
    conn.close()

def get_ute_math(salary, months_paid):
    """
    The UTE Formula:
    - Platform Fee: 3% (Added on top)
    - Month 1: 20% to You, 10% Cashback to Employer.
    - Month 2-12: 6% to You, 4% Cashback to Employer.
    """
    fee = salary * 0.03
    total_charged = salary + fee
    if months_paid == 0:
        return {"total": total_charged, "ute": salary * 0.20, "cashback": salary * 0.10, "net": salary * 0.70, "pct": 30}
    return {"total": total_charged, "ute": salary * 0.06, "cashback": salary * 0.04, "net": salary * 0.90, "pct": 10}
