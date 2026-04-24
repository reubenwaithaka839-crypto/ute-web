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
    
    # Users Table (Added skills, expected_salary for talents.html to work without crashing)
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, contacts TEXT, 
        passcode TEXT, role TEXT, is_admin INTEGER DEFAULT 0, equity_acc TEXT,
        balance REAL DEFAULT 0.0, location TEXT, bio_or_company TEXT, skills TEXT,
        expected_salary REAL, photo_url TEXT,
        business_reg_no TEXT, is_verified_business INTEGER DEFAULT 0)""")
        
    # Jobs Table (Added description so it doesn't crash)
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY, title TEXT, description TEXT, salary REAL, 
        poster TEXT, status TEXT DEFAULT 'active')""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, room_id TEXT, sender TEXT, text TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY, job_id INTEGER, applicant_username TEXT,
        full_name TEXT, age INTEGER, gender TEXT, phone TEXT, email TEXT,
        photo_url TEXT, skills TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY, sender TEXT, receiver TEXT, amount REAL,
        type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    # THE ADMIN GOD: REUBEN
    cur.execute("INSERT OR IGNORE INTO users (username, passcode, role, is_admin, is_verified_business) VALUES ('REUBEN', 'GOD_MODE_2026', 'admin', 1, 1)")
    
    conn.commit()
    conn.close()
