import sqlite3

class UTE:
    def __init__(self):
        self.conn = sqlite3.connect("ute.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.create_tables()
        self.create_wallet_table()

    # ================= TABLES =================
    def create_tables(self):
        # USERS
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            password BLOB,
            role TEXT
        )
        """)

        # USER BANK DETAILS
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_bank_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            role TEXT,
            bank_name TEXT,
            account_name TEXT,
            account_number TEXT
        )
        """)

        # ADMIN BANK
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT,
            account_name TEXT,
            account_number TEXT
        )
        """)

        self.conn.commit()

    # ================= WALLET SYSTEM =================
    def create_wallet_table(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT UNIQUE,
            balance REAL DEFAULT 0
        )
        """)
        self.conn.commit()

    def init_wallet(self, user):
        self.cursor.execute("""
        INSERT OR IGNORE INTO wallets (user, balance)
        VALUES (?, 0)
        """, (user,))
        self.conn.commit()

    def get_balance(self, user):
        self.cursor.execute("""
        SELECT balance FROM wallets WHERE user=?
        """, (user,))
        result = self.cursor.fetchone()
        return result[0] if result else 0

    def update_balance(self, user, amount):
        self.cursor.execute("""
        UPDATE wallets
        SET balance = balance + ?
        WHERE user=?
        """, (amount, user))
        self.conn.commit()

    # ================= USERS =================
    def register_user(self, name, password, role):
        try:
            self.cursor.execute("""
            INSERT INTO users (name, password, role)
            VALUES (?, ?, ?)
            """, (name, password, role))
            self.conn.commit()

            # AUTO CREATE WALLET
            self.init_wallet(name)

        except:
            pass  # user exists

    def get_user(self, name):
        self.cursor.execute("""
        SELECT * FROM users WHERE name=?
        """, (name,))
        return self.cursor.fetchone()

    # ================= USER BANK =================
    def save_user_bank(self, user, role, bank, acc_name, acc_number):
        self.cursor.execute("""
        INSERT INTO user_bank_details (user, role, bank_name, account_name, account_number)
        VALUES (?, ?, ?, ?, ?)
        """, (user, role, bank, acc_name, acc_number))
        self.conn.commit()

    def get_user_bank(self, user):
        self.cursor.execute("""
        SELECT bank_name, account_name, account_number
        FROM user_bank_details
        WHERE user=?
        """, (user,))
        return self.cursor.fetchone()

    # ================= ADMIN BANK =================
    def save_admin_bank(self, bank, name, number):
        self.cursor.execute("DELETE FROM admin_bank")
        self.cursor.execute("""
        INSERT INTO admin_bank (bank_name, account_name, account_number)
        VALUES (?, ?, ?)
        """, (bank, name, number))
        self.conn.commit()

    def get_admin_bank(self):
        self.cursor.execute("""
        SELECT bank_name, account_name, account_number
        FROM admin_bank
        LIMIT 1
        """)
        return self.cursor.fetchone()

    # ================= CLOSE =================
    def close(self):
        self.conn.close()
