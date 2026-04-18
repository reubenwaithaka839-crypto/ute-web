import sqlite3

DB = "ute.db"

# ---------------- INIT DB ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    # WALLET
    c.execute("""
    CREATE TABLE IF NOT EXISTS wallet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
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
        salary REAL
    )
    """)

    conn.commit()
    conn.close()


# ---------------- ADD JOB ----------------
def add_job(employer, title, description, requirements, location, salary):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    INSERT INTO jobs (employer, title, description, requirements, location, salary)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (employer, title, description, requirements, location, salary))

    conn.commit()
    conn.close()

    print(f"📢 JOB POSTED → {title}")


# ---------------- GET JOBS ----------------
def get_jobs():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM jobs ORDER BY id DESC")
    jobs = c.fetchall()

    conn.close()
    return jobs


# ---------------- START ----------------
init_db()
