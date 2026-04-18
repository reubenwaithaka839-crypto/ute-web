import sqlite3
DB = "ute.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY, username TEXT UNIQUE, balance REAL DEFAULT 0)")
    c.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, employer TEXT, title TEXT, description TEXT, requirements TEXT, location TEXT, salary REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, job_id INTEGER, applicant TEXT, status TEXT DEFAULT 'pending')")
    conn.commit()
    conn.close()

def get_balance(user):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT balance FROM wallet WHERE username=?", (user,)).fetchone()
    conn.close()
    return row[0] if row else 0

def add_job(employer, title, desc, req, loc, salary):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO jobs (employer, title, description, requirements, location, salary) VALUES (?,?,?,?,?,?)", (employer, title, desc, req, loc, salary))
    conn.commit()
    conn.close()

def get_jobs():
    conn = sqlite3.connect(DB)
    jobs = conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    conn.close()
    return jobs

def apply_job(job_id, user):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO applications (job_id, applicant) VALUES (?, ?)", (job_id, user))
    conn.commit()
    conn.close()
