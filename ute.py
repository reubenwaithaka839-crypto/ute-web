import os
import sqlite3
from cryptography.fernet import Fernet

DB = "rw_prestige_final.db"
# Security Key for logic protection
KEY = os.environ.get('LOGIC_KEY', Fernet.generate_key().decode())
cipher = Fernet(KEY.encode())

def calculate_prestige_split(gross_salary, is_first_month=True):
    """
    IMPLEMENTING YOUR MULTI-PARTY EARNING MODEL:
    1. 3% Transaction Fee (Treasury)
    2. Registration Fee: 100 KES (Treasury)
    3. First Month: 30% Deduction (Split between Treasury & Employer)
    4. Monthly: 10% Deduction (Split between Treasury & Employer)
    """
    total_gross = float(gross_salary)
    transaction_fee = total_gross * 0.03 # 3% on every movement
    
    if is_first_month:
        # 30% Deduction Logic
        total_deduction = total_gross * 0.30
        employee_earns = total_gross * 0.70
        
        # Employer earns 10% of first salary back from the 30%
        employer_rebate = total_gross * 0.10
        # Treasury keeps the remaining 20%
        treasury_cut = total_deduction - employer_rebate
    else:
        # 10% Deduction Logic (Monthly for 1 year)
        total_deduction = total_gross * 0.10
        employee_earns = total_gross * 0.90
        
        # Employer earns 2% back from the 10%
        employer_rebate = total_gross * 0.02
        # Treasury keeps 8%
        treasury_cut = total_deduction - employer_rebate

    return {
        "gross": total_gross,
        "transaction_fee": transaction_fee,
        "employee_net": employee_earns,
        "employer_rebate": employer_rebate,
        "treasury_total": treasury_cut + transaction_fee
    }

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # Users, Jobs, and the new CHAT table
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, passcode TEXT, role TEXT, balance REAL DEFAULT 0, kra_pin TEXT, equity_acc TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, title TEXT, salary REAL, poster TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, job_id INTEGER, applicant TEXT, status TEXT DEFAULT 'pending')")
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, 
        room_id TEXT, 
        sender TEXT, 
        text TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()
