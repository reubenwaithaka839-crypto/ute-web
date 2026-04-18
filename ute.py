import sqlite3

DB = "ute.db"

# ================= INIT DB =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # WALLET
    c.execute("""
    CREATE TABLE IF NOT EXISTS wallet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        balance REAL DEFAULT 0
    )
    """)

    # JOBS
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

    # APPLICATIONS
    c.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        applicant TEXT,
        status TEXT DEFAULT 'pending'
    )
    """)

    # TRANSACTIONS
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


# ================= WALLET =================
def update_balance(user, amount):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("UPDATE wallet SET balance = balance + ? WHERE username=?", (amount, user))

    conn.commit()
    conn.close()


def get_balance(user):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT balance FROM wallet WHERE username=?", (user,))
    row = c.fetchone()

    conn.close()
    return row[0] if row else 0


# ================= JOBS =================
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

    c.execute("SELECT * FROM jobs ORDER BY id DESC")
    jobs = c.fetchall()

    conn.close()
    return jobs


# ================= APPLICATIONS =================
def apply_job(job_id, user):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO applications (job_id, applicant)
    VALUES (?, ?)
    """, (job_id, user))

    conn.commit()
    conn.close()
