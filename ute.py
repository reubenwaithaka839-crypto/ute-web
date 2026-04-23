import os
import sqlite3
from cryptography.fernet import Fernet

DB = "rw_prestige_final.db"
KEY = os.environ.get('LOGIC_KEY', Fernet.generate_key().decode())
cipher = Fernet(KEY.encode())

def calculate_prestige_split(gross, is_first=True):
    gross = float(gross)
    fee = gross * 0.03
    if is_first:
        emp_net = gross * 0.70
        rebate = gross * 0.10
        treasury = (gross * 0.20) + fee
    else:
        emp_net = gross * 0.90
        rebate = gross * 0.02
        treasury = (gross * 0.08) + fee
    return {"employee_net": round(emp_net, 2), "employer_rebate": round(rebate, 2), "treasury_total": round(treasury, 2)}

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # Updated User Table with Contacts and Admin status
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT UNIQUE, 
        email TEXT,
        contacts TEXT,
        passcode TEXT, 
        role TEXT, 
        is_admin INTEGER DEFAULT 0,
        equity_acc TEXT,
        kra_pin TEXT)""")
    
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, title TEXT, salary REAL, poster TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, job_id INTEGER, applicant TEXT, status TEXT DEFAULT 'pending')")
    cur.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, room_id TEXT, sender TEXT, text TEXT, photo_url TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    
    # Create the 'Admin God' if not exists
    cur.execute("INSERT OR IGNORE INTO users (username, passcode, role, is_admin) VALUES ('REUBEN', 'GOD_MODE_2026', 'admin', 1)")
    
    conn.commit()
    conn.close()
