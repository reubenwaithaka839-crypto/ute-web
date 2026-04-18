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
            password TEXT,
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

        # TRANSACTIONS
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            receiver TEXT,
            amount REAL,
            type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    # ================= USERS =================
    def register_company(self, name, password):
        self.cursor.execute("""
        INSERT OR IGNORE INTO users (name, password, role)
        VALUES (?, ?, ?)
        """, (name, password, "company"))

        self.conn.commit()
        self.init_wallet(name)

    def login_company(self, name, password):
        self.cursor.execute("""
        SELECT * FROM users WHERE name=? AND password=?
        """, (name, password))

        return self.cursor.fetchone()

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

    # ================= PAYROLL / TRANSFER =================
    def process_salary(self, sender, receiver, amount, approved=True):

        amount = float(amount)

        if self.get_balance(sender) >= amount:

            # debit sender
            self.update_balance(sender, -amount)

            # credit receiver
            self.update_balance(receiver, amount)

            # log transaction
            self.log_transaction(sender, receiver, amount, "PAYROLL")

            return True

        return False

    # ================= TRANSACTIONS =================
    def log_transaction(self, sender, receiver, amount, type_):
        self.cursor.execute("""
        INSERT INTO transactions (sender, receiver, amount, type)
        VALUES (?, ?, ?, ?)
        """, (sender, receiver, amount, type_))

        self.conn.commit()

    def get_transactions(self):
        self.cursor.execute("""
        SELECT sender, receiver, amount, type
        FROM transactions
        ORDER BY id DESC
        """)

        return self.cursor.fetchall()

    # ================= JOBS (STATIC SAMPLE) =================
    def get_jobs(self):
        return [
            {"title": "Electrician", "location": "Nairobi", "salary": 20000},
            {"title": "Driver", "location": "Mombasa", "salary": 15000},
            {"title": "Clerk", "location": "Kisumu", "salary": 12000}
        ]

    # ================= ADMIN REVENUE =================
    def get_revenue(self):
        self.cursor.execute("""
        SELECT SUM(amount) FROM transactions WHERE type='PAYROLL'
        """)

        res = self.cursor.fetchone()[0]
        return res if res else 0

    # ================= EMPLOYEES (PLACEHOLDER) =================
    def get_company_employees(self, company):
        return [
            ("John Doe", "6 months"),
            ("Jane Smith", "3 months"),
            ("Mike Johnson", "1 year")
        ]
