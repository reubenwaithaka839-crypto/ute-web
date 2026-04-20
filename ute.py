import sqlite3
import os

# Database file name
DB = "ute.db"

def init_db():
    """
    Initializes the database and creates all necessary tables for the 
    Closed-Loop Recruitment & Escrow Economy.
    """
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    
    # 1. USERS TABLE: Stores Identities (Employees & Employers)
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, 
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        national_id TEXT UNIQUE,
        password TEXT, 
        role TEXT, 
        location TEXT,
        skills TEXT
    )""")
    
    # 2. JOBS TABLE: For the 'Modern Marketplace' (Employer posts, Employee sees)
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employer TEXT, 
        title TEXT, 
        description TEXT, 
        salary REAL,
        status TEXT DEFAULT 'open',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # 3. CONTRACTS TABLE: Tracks active hire agreements and 12-month loyalty
    c.execute("""CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employer TEXT, 
        employee TEXT, 
        salary REAL, 
        total_months_paid INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active'
    )""")
    
    # 4. WALLET TABLE: Tracks the digital escrow balances
    c.execute("""CREATE TABLE IF NOT EXISTS wallet (
        username TEXT UNIQUE, 
        balance REAL DEFAULT 0
    )""")
    
    conn.commit()
    conn.close()

# AUTO-INITIALIZE: This ensures tables are created the moment the app starts
init_db()

def get_ute_math(salary, months_paid):
    """
    Calculates the UTE revenue splits based on the 30/10 rule:
    - Month 1: 30% Fee (20% UTE, 10% Employer Cashback)
    - Month 2-12: 10% Fee (6% UTE, 4% Employer Cashback)
    - 3% Transaction Protection is added on top of the base salary.
    """
    # 3% Transaction Protection Fee (Paid by Employer)
    protection_fee = salary * 0.03
    total_to_pay = salary + protection_fee
    
    if months_paid == 0:
        # Month 1 Placement (30% total split)
        return {
            "total": total_to_pay, 
            "ute": salary * 0.20, 
            "cashback": salary * 0.10, 
            "net": salary * 0.70
        }
    else:
        # Month 2-12 Loyalty (10% total split)
        return {
            "total": total_to_pay, 
            "ute": salary * 0.06, 
            "cashback": salary * 0.04, 
            "net": salary * 0.90
        }
