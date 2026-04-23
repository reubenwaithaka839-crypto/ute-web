import os
import sqlite3
from cryptography.fernet import Fernet

DB = "rw_prestige_final.db"
# Security Key for logic protection
KEY = os.environ.get('LOGIC_KEY', Fernet.generate_key().decode())
cipher = Fernet(KEY.encode())

def calculate_prestige_split(gross_salary, is_first_month=True):
    total_gross = float(gross_salary)
    transaction_fee = total_gross * 0.03 # 3% on every movement
    
    if is_first_month:
        # 30% Deduction Logic
        total_deduction = total_gross * 0.30
        employee_earns = total_gross * 0.70
        employer_rebate = total_gross * 0.10
        treasury_cut = total_deduction - employer_rebate
    else:
        # 10% Deduction Logic
        total_deduction = total_gross * 0.10
        employee_earns = total_gross * 0.90
        employer_rebate = total_gross * 0.02
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
    # Users: Added equity_acc and kra_pin per your requirement
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, 
        passcode TEXT, 
        role TEXT, 
        balance REAL DEFAULT 0, 
        kra_pin TEXT, 
        equity_acc TEXT)""")
    
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, salary REAL, poster TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER, applicant TEXT, status TEXT DEFAULT 'pending')")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        room_id TEXT, 
        sender TEXT, 
        text TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    
    # Ensure at least one Admin exists for testing
    cur.execute("INSERT OR IGNORE INTO users (username, passcode, role, balance) VALUES (?,?,?,?)", 
                ('admin', '1234', 'admin', 0.0))
    
    conn.commit()
    conn.close()
