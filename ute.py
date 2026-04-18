import sqlite3

DB = "ute.db"

# ================= DATABASE INITIALIZATION =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # USERS TABLE (Added unique constraint on username)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # WALLET TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS wallet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        balance REAL DEFAULT 0
    )
    """)

    # JOBS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer TEXT,
        title TEXT,
        description TEXT,
        requirements TEXT,
        location TEXT,
        salary REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # APPLICATIONS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        applicant TEXT,
        status TEXT DEFAULT 'pending',
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # TRANSACTIONS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


# ================= WALLET LOGIC =================
def update_balance(user, amount):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Using 'INSERT OR IGNORE' ensures that if a wallet doesn't exist yet, it won't crash
    c.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (user,))
    c.execute("UPDATE wallet SET balance = balance + ? WHERE username=?", (amount, user))
    conn.commit()
    conn.close()


def get_balance(user):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT balance FROM wallet WHERE username=?", (user,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0.0


# ================= JOB LOGIC =================
def add_job(employer, title, description, requirements, location, salary):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    INSERT INTO jobs (employer, title, description, requirements, location, salary)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (employer, title, description, requirements, location, salary))
    conn.commit()
    conn.close()


def get_jobs():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Fetching jobs with the most recent first
    c.execute("SELECT * FROM jobs ORDER BY id DESC")
    jobs = c.fetchall()
    conn.close()
    return jobs


# ================= APPLICATIONS LOGIC =================
def apply_job(job_id, user):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Check if already applied to prevent duplicates
    c.execute("SELECT id FROM applications WHERE job_id=? AND applicant=?", (job_id, user))
    if c.fetchone() is None:
        c.execute("""
        INSERT INTO applications (job_id, applicant)
        VALUES (?, ?)
        """, (job_id, user))
        conn.commit()
    conn.close()

def get_user_applications(user):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Joins applications with jobs so the user can see the title of what they applied for
    c.execute("""
    SELECT j.title, j.location, a.status, a.applied_at 
    FROM applications a 
    JOIN jobs j ON a.job_id = j.id 
    WHERE a.applicant = ?
    """, (user,))
    apps = c.fetchall()
    conn.close()
    return apps
