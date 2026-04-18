import sqlite3

class UTE:
    def __init__(self):
        self.conn = sqlite3.connect("ute.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    # ================= DATABASE =================
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

        # WALLETS
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT UNIQUE,
            balance REAL DEFAULT 0
        )
        """)

        # PAYROLL
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employer TEXT,
            employee TEXT,
            salary REAL
        )
        """)

        # MPESA TRANSACTIONS
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS mpesa_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT,
            amount REAL,
            status TEXT,
            receipt TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # FRAUD LOGS
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS fraud_flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            reason TEXT,
            amount REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # ML DATASET (FOR AI TRAINING)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS fraud_dataset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            amount REAL,
            is_fraud INTEGER
        )
        """)

        self.conn.commit()

    # ================= USERS =================
    def register_user(self, name, password, role):
        self.cursor.execute("""
        INSERT OR IGNORE INTO users (name, password, role)
        VALUES (?, ?, ?)
        """, (name, password, role))
        self.conn.commit()

        self.init_wallet(name)

    # ================= WALLET =================
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
        res = self.cursor.fetchone()
        return res[0] if res else 0

    def update_balance(self, user, amount):
        self.cursor.execute("""
        UPDATE wallets SET balance = balance + ? WHERE user=?
        """, (amount, user))
        self.conn.commit()

    def withdraw(self, user, amount):
        if self.get_balance(user) >= amount:
            self.update_balance(user, -amount)
            return True
        return False

    # ================= TRANSFER =================
    def transfer_with_commission(self, sender, receiver, amount):
        if sender == receiver:
            self.flag_fraud(sender, "Self transfer attempt", amount)
            return False

        if self.get_balance(sender) < amount:
            return False

        commission = amount * 0.02
        receive = amount - commission

        self.update_balance(sender, -amount)
        self.update_balance(receiver, receive)
        self.update_balance("admin", commission)

        return True

    # ================= PAYROLL =================
    def set_salary(self, employer, employee, salary):
        self.cursor.execute("""
        INSERT INTO payroll (employer, employee, salary)
        VALUES (?, ?, ?)
        """, (employer, employee, salary))
        self.conn.commit()

    def run_payroll(self):
        self.cursor.execute("SELECT employer, employee, salary FROM payroll")
        data = self.cursor.fetchall()

        for employer, employee, salary in data:
            if self.get_balance(employer) >= salary:
                self.update_balance(employer, -salary)
                self.update_balance(employee, salary)

        self.conn.commit()

    def get_all_payroll(self):
        self.cursor.execute("SELECT employer, employee, salary FROM payroll")
        return self.cursor.fetchall()

    def get_total_payroll_amount(self):
        self.cursor.execute("SELECT SUM(salary) FROM payroll")
        res = self.cursor.fetchone()[0]
        return res if res else 0

    # ================= MPESA =================
    def save_mpesa(self, phone, amount, status, receipt):
        self.cursor.execute("""
        INSERT INTO mpesa_transactions (phone, amount, status, receipt)
        VALUES (?, ?, ?, ?)
        """, (phone, amount, status, receipt))
        self.conn.commit()

    # ================= FRAUD =================
    def flag_fraud(self, user, reason, amount):
        self.cursor.execute("""
        INSERT INTO fraud_flags (user, reason, amount)
        VALUES (?, ?, ?)
        """, (user, reason, amount))
        self.conn.commit()

    def get_fraud_logs(self):
        self.cursor.execute("""
        SELECT user, reason, amount FROM fraud_flags
        ORDER BY id DESC
        """)
        return self.cursor.fetchall()

    # ================= ML DATA =================
    def log_ml_data(self, sender, receiver, amount, is_fraud):
        self.cursor.execute("""
        INSERT INTO fraud_dataset (sender, receiver, amount, is_fraud)
        VALUES (?, ?, ?, ?)
        """, (sender, receiver, amount, is_fraud))
        self.conn.commit()

    def get_ml_data(self):
        self.cursor.execute("""
        SELECT sender, receiver, amount, is_fraud FROM fraud_dataset
        """)
        return self.cursor.fetchall()

    # ================= ADMIN ANALYTICS =================
    def get_total_users(self):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        return self.cursor.fetchone()[0]

    def get_total_system_balance(self):
        self.cursor.execute("SELECT SUM(balance) FROM wallets")
        res = self.cursor.fetchone()[0]
        return res if res else 0

    def get_admin_earnings(self):
        self.cursor.execute("""
        SELECT balance FROM wallets WHERE user='admin'
        """)
        res = self.cursor.fetchone()
        return res[0] if res else 0
