import sqlite3
import bcrypt

class UTE:
    def __init__(self):
        self.conn = sqlite3.connect("ute.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_database()

    # =========================
    # 🗄️ DATABASE
    # =========================
    def setup_database(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            name TEXT PRIMARY KEY,
            password BLOB
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            name TEXT,
            months INTEGER
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            employee TEXT,
            salary REAL,
            deduction REAL,
            fee REAL,
            total_gain REAL
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS system (
            key TEXT PRIMARY KEY,
            value REAL
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

        self.cursor.execute(
            "INSERT OR IGNORE INTO system (key, value) VALUES ('revenue', 0)"
        )

        self.conn.commit()

    # =========================
    # 🔐 AUTH (SECURE)
    # =========================
    def register_company(self, name, password):
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            self.cursor.execute(
                "INSERT INTO companies VALUES (?, ?)",
                (name, hashed)
            )

            self.conn.commit()
            return True
        except:
            return False

    def login_company(self, name, password):
        self.cursor.execute(
            "SELECT password FROM companies WHERE name=?",
            (name,)
        )

        result = self.cursor.fetchone()

        if not result:
            return False

        stored_hash = result[0]

        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')

        return bcrypt.checkpw(
            password.encode('utf-8'),
            stored_hash
        )

    # =========================
    # 💰 SALARY ENGINE
    # =========================
    def process_salary(self, company, employee, salary, first_time=False):
        try:
            salary = float(salary)
        except:
            return False

        if salary <= 0:
            return False

        self.cursor.execute(
            "SELECT * FROM employees WHERE company=? AND name=?",
            (company, employee)
        )

        emp = self.cursor.fetchone()

        if not emp:
            deduction = salary * 0.30
            months = 1

            self.cursor.execute(
                "INSERT INTO employees (company, name, months) VALUES (?, ?, ?)",
                (company, employee, months)
            )
        else:
            deduction = salary * 0.10
            months = emp[3] + 1

            self.cursor.execute(
                "UPDATE employees SET months=? WHERE id=?",
                (months, emp[0])
            )

        fee = salary * 0.02
        total_gain = deduction + fee

        self.cursor.execute(
            "UPDATE system SET value = value + ? WHERE key='revenue'",
            (total_gain,)
        )

        self.cursor.execute("""
            INSERT INTO transactions (company, employee, salary, deduction, fee, total_gain)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company, employee, salary, deduction, fee, total_gain))

        self.conn.commit()
        return True

    # =========================
    # 📊 DATA
    # =========================
    def get_company_employees(self, company):
        self.cursor.execute(
            "SELECT name, months FROM employees WHERE company=?",
            (company,)
        )
        return self.cursor.fetchall()

    def get_transactions(self):
        self.cursor.execute(
            "SELECT company, employee, total_gain FROM transactions"
        )
        return self.cursor.fetchall()

    def get_revenue(self):
        self.cursor.execute(
            "SELECT value FROM system WHERE key='revenue'"
        )
        return round(self.cursor.fetchone()[0], 2)

    # =========================
    # 📈 STATS
    # =========================
    def get_total_companies(self):
        self.cursor.execute("SELECT COUNT(*) FROM companies")
        return self.cursor.fetchone()[0]

    def get_total_workers(self):
        self.cursor.execute("SELECT COUNT(*) FROM employees")
        return self.cursor.fetchone()[0]

    # =========================
    # 👷 JOBS
    # =========================
    def get_jobs(self):
        return [
            {"title": "Software Developer", "location": "Nairobi", "salary": 80000},
            {"title": "Accountant", "location": "Mombasa", "salary": 60000},
            {"title": "Driver", "location": "Kisumu", "salary": 40000},
            {"title": "Designer", "location": "Remote", "salary": 70000}
        ]

    # =========================
    # 🏦 BANK DETAILS
    # =========================
    def save_bank_details(self, bank_name, account_name, account_number):
        self.cursor.execute("DELETE FROM admin_bank")
        self.cursor.execute("""
            INSERT INTO admin_bank (bank_name, account_name, account_number)
            VALUES (?, ?, ?)
        """, (bank_name, account_name, account_number))

        self.conn.commit()

    def get_bank_details(self):
        self.cursor.execute("""
            SELECT bank_name, account_name, account_number
            FROM admin_bank
            LIMIT 1
        """)
        return self.cursor.fetchone()