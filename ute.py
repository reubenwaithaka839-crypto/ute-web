import sqlite3
import os
from datetime import datetime

DB = "ute.db"

# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def connect():
    conn = sqlite3.connect(DB)
    return conn

# -----------------------------
# INITIALIZE DATABASE
# -----------------------------
def init_db():
    conn = connect()
    c = conn.cursor()

    print("🚀 Initializing UTE Database...")

    # USERS TABLE
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

    # TRANSACTIONS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        type TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

    print("✅ DATABASE READY (users + wallet + transactions)")

# -----------------------------
# WALLET FUNCTIONS
# -----------------------------
def get_balance(username):
    conn = connect()
    c = conn.cursor()

    c.execute("SELECT balance FROM wallet WHERE username=?", (username,))
    row = c.fetchone()

    conn.close()
    return row[0] if row else 0


def update_balance(username, amount):
    conn = connect()
    c = conn.cursor()

    c.execute("""
    UPDATE wallet
    SET balance = balance + ?
    WHERE username=?
    """, (amount, username))

    conn.commit()
    conn.close()

    print(f"💰 BALANCE UPDATED → {username}: +{amount}")

# -----------------------------
# TRANSACTIONS
# -----------------------------
def add_transaction(sender, receiver, amount, tx_type):
    conn = connect()
    c = conn.cursor()

    c.execute("""
    INSERT INTO transactions (sender, receiver, amount, type, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        sender,
        receiver,
        amount,
        tx_type,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    print(f"📊 TRANSACTION LOGGED → {sender} → {receiver} | {amount} | {tx_type}")

# -----------------------------
# SYSTEM START MESSAGE
# -----------------------------
def start_system():
    print("===================================")
    print("💼 UTE FINTECH SYSTEM STARTING...")
    print("===================================")

    init_db()

    print("✅ SYSTEM READY")

# -----------------------------
# RUN DIRECTLY
# -----------------------------
if __name__ == "__main__":
    start_system()
