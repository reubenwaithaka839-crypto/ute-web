import sqlite3

class UTE:
    def __init__(self):
        self.conn = sqlite3.connect("ute.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.create_tables()
        self.create_wallet_table()

    # ================= CORE TABLES =================
    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            password BLOB,
            role TEXT
        )
        """)

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

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT,
            account_name TEXT,
            account_number TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employer TEXT,
            employee TEXT,
            salary REAL
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

    # ================= WITHDRAW =================
    def withdraw(self, user, amount):
        balance = self.get_balance(user)

        if balance >= amount:
            self.cursor.execute("""
            UPDATE wallets
            SET balance = balance - ?
            WHERE user=?
            """, (amount, user))
            self.conn.commit()
            return True
        return False

    # ================= PAYMENTS (WITH COMMISSION) =================
    def transfer_with_commission(self, sender, receiver, amount, commission_rate=0.02):
        sender_balance = self.get_balance(sender)

        if sender_balance >= amount:
            commission = amount * commission_rate
            receiver_amount = amount - commission

            # deduct sender
            self.cursor.execute("""
            UPDATE wallets
            SET balance = balance - ?
            WHERE user=?
            """, (amount, sender))

            # credit receiver
            self.cursor.execute("""
            UPDATE wallets
            SET balance = balance + ?
            WHERE user=?
            """, (receiver_amount, receiver))

            # credit admin
            self.cursor.execute("""
            UPDATE wallets
            SET balance = balance + ?
            WHERE user=?
            """, (commission, "admin"))

            self.conn.commit()
            return True

        return False

    # ================= USERS =================
    def register_user(self, name, password, role):
        try:
            self.cursor.execute("""
            INSERT INTO users (name, password, role)
            VALUES (?, ?, ?)
            """, (name, password, role))
            self.conn.commit()

            self.init_wallet(name)

        except:
            pass

        if role == "admin":
            self.init_wallet(name)

    def get_user(self, name):
        self.cursor.execute("""
        SELECT * FROM users WHERE name=?
        """, (name,))
        return self.cursor.fetchone()

    # ================= BANK DETAILS =================
    def save_user_bank(self, user, role, bank, acc_name, acc_number):
        self.cursor.execute("""
        INSERT INTO user_bank_details (user, role, bank_name, account_name, account_number)
        VALUES (?, ?, ?, ?, ?)
        """, (user, role, bank, acc_name, acc_number))
        self.conn.commit()

    def save_admin_bank(self, bank, name, number):
        self.cursor.execute("DELETE FROM admin_bank")
        self.cursor.execute("""
        INSERT INTO admin_bank (bank_name, account_name, account_number)
        VALUES (?, ?, ?)
        """, (bank, name, number))
        self.conn.commit()

    # ================= PAYROLL SYSTEM =================
    def set_salary(self, employer, employee, salary):
        self.cursor.execute("""
        INSERT INTO payroll (employer, employee, salary)
        VALUES (?, ?, ?)
        """, (employer, employee, salary))
        self.conn.commit()

    def run_payroll(self):
        self.cursor.execute("SELECT employer, employee, salary FROM payroll")
        records = self.cursor.fetchall()

        for employer, employee, salary in records:
            if self.get_balance(employer) >= salary:
                # deduct employer
                self.cursor.execute("""
                UPDATE wallets
                SET balance = balance - ?
                WHERE user=?
                """, (salary, employer))

                # credit employee
                self.cursor.execute("""
                UPDATE wallets
                SET balance = balance + ?
                WHERE user=?
                """, (salary, employee))

        self.conn.commit()

    def get_all_payroll(self):
        self.cursor.execute("""
        SELECT employer, employee, salary FROM payroll
        """)
        return self.cursor.fetchall()

    def get_total_payroll_amount(self):
        self.cursor.execute("""
        SELECT SUM(salary) FROM payroll
        """)
        result = self.cursor.fetchone()[0]
        return result if result else 0

    # ================= ADMIN STATS =================
    def get_total_users(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

    def get_total_system_balance(self):
        self.cursor.execute("SELECT SUM(balance) FROM wallets")
        result = self.cursor.fetchone()[0]
        return result if result else 0

    def get_admin_earnings(self):
        self.cursor.execute("""
        SELECT balance FROM wallets WHERE user='admin'
        """)
        result = self.cursor.fetchone()
        return result[0] if result else 0

    # ================= CLOSE =================
    def close(self):
        self.conn.close()
