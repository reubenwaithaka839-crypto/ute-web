import os
import sqlite3

DB = "rw_prestige_final.db"

def calculate_prestige_split(gross, is_first=True):
    gross = float(gross)
    fee = gross * 0.03
    if is_first:
        emp_net, rebate, treasury = gross * 0.70, gross * 0.10, (gross * 0.20) + fee
    else:
        emp_net, rebate, treasury = gross * 0.90, gross * 0.02, (gross * 0.08) + fee
    return {"employee_net": round(emp_net, 2), "employer_rebate": round(rebate, 2), "treasury_total": round(treasury, 2)}

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, contacts TEXT, 
        passcode TEXT, role TEXT, is_admin INTEGER DEFAULT 0, equity_acc TEXT)""")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, title TEXT, salary REAL, poster TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, room_id TEXT, sender TEXT, text TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    
    # THE ADMIN GOD: REUBEN
    cur.execute("INSERT OR IGNORE INTO users (username, passcode, role, is_admin) VALUES ('REUBEN', 'GOD_MODE_2026', 'admin', 1)")
    conn.commit()
    conn.close()
