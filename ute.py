import sqlite3
from datetime import datetime

DB = "ute.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Fixed columns to match the registration form
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT, 
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        national_id TEXT UNIQUE,
        password TEXT, 
        role TEXT, 
        location TEXT,
        skills TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY, 
        employer TEXT, 
        employee TEXT, 
        salary REAL, 
        total_months_paid INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS wallet (
        username TEXT UNIQUE, 
        balance REAL DEFAULT 0
    )""")
    conn.commit()
    conn.close()

def get_ute_math(salary, months_paid):
    fee = salary * 0.03
    total = salary + fee
    if months_paid == 0:
        return {"total": total, "ute": salary * 0.20, "cashback": salary * 0.10, "net": salary * 0.70}
    return {"total": total, "ute": salary * 0.06, "cashback": salary * 0.04, "net": salary * 0.90}
