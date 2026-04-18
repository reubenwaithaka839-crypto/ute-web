from flask import Flask, request, session, redirect, jsonify
import sqlite3
import os
import time
from mpesa import Mpesa

app = Flask(__name__)
app.secret_key = "ute-secret-key"

# ================= ENV VARIABLES =================
CONSUMER_KEY = os.environ.get("MPESA_KEY")
CONSUMER_SECRET = os.environ.get("MPESA_SECRET")
SHORTCODE = os.environ.get("MPESA_SHORTCODE")
PASSKEY = os.environ.get("MPESA_PASSKEY")

mpesa = Mpesa(
    CONSUMER_KEY,
    CONSUMER_SECRET,
    SHORTCODE,
    PASSKEY,
    "https://sandbox.safaricom.co.ke"
)

# ================= RATE LIMIT =================
last_request = {}

def rate_limit(user):
    now = time.time()

    if user in last_request:
        if now - last_request[user] < 10:
            return False

    last_request[user] = now
    return True

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("ute.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        password TEXT,
        role TEXT,
        balance REAL DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        type TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer TEXT,
        employee TEXT,
        amount REAL,
        status TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS processed_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checkout_id TEXT UNIQUE
    )""")

    conn.commit()
    conn.close()

init_db()

# ================= WALLET =================
def update_balance(user, amount):
    conn = sqlite3.connect("ute.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE name=?", (amount, user))
    conn.commit()
    conn.close()

def get_balance(user):
    conn = sqlite3.connect("ute.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE name=?", (user,))
    data = c.fetchone()
    conn.close()
    return data[0] if data else 0

# ================= HOME =================
@app.route("/")
def home():
    return "<h1>UTE FINTECH SYSTEM</h1><a href='/auth'>Start</a>"

# ================= AUTH =================
@app.route("/auth", methods=["GET", "POST"])
def auth():

    if request.method == "POST":

        name = request.form["name"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("ute.db")
        c = conn.cursor()

        c.execute("INSERT INTO users (name, password, role, balance) VALUES (?, ?, ?, ?)",
                  (name, password, role, 0))

        conn.commit()
        conn.close()

        session["user"] = name
        session["role"] = role

        return redirect("/dashboard")

    return """
    <form method="post">
        <input name="name" placeholder="Name">
        <input name="password" type="password">
        <select name="role">
            <option value="admin">Admin</option>
            <option value="employer">Employer</option>
            <option value="employee">Employee</option>
        </select>
        <button>Create</button>
    </form>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    user = session.get("user")
    role = session.get("role")

    balance = get_balance(user)

    return f"""
    <h2>{user} ({role})</h2>
    <h3>Balance: {balance}</h3>

    <a href='/payroll'>Payroll</a><br>
    <a href='/deposit'>M-Pesa</a>
    """

# ================= PAYROLL =================
@app.route("/payroll", methods=["GET", "POST"])
def payroll():

    if request.method == "POST":

        employer = session["user"]
        employee = request.form["employee"]
        amount = float(request.form["amount"])

        update_balance(employee, amount)

        conn = sqlite3.connect("ute.db")
        c = conn.cursor()

        c.execute("INSERT INTO payroll (employer, employee, amount, status) VALUES (?, ?, ?, ?)",
                  (employer, employee, amount, "PAID"))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return """
    <form method="post">
        <input name="employee" placeholder="Employee">
        <input name="amount" placeholder="Amount">
        <button>Pay</button>
    </form>
    """

# ================= STK PUSH =================
@app.route("/stk", methods=["POST"])
def stk():

    phone = request.form["phone"]
    amount = request.form["amount"]

    if not rate_limit(phone):
        return {"error": "Too many requests"}, 429

    res = mpesa.stk_push(
        phone,
        amount,
        "https://your-app.onrender.com/callback"
    )

    return jsonify(res)

# ================= CALLBACK =================
@app.route("/callback", methods=["POST"])
def callback():

    data = request.json

    try:
        stk = data["Body"]["stkCallback"]

        if stk["ResultCode"] == 0:

            checkout_id = stk["CheckoutRequestID"]

            conn = sqlite3.connect("ute.db")
            c = conn.cursor()

            c.execute("SELECT * FROM processed_payments WHERE checkout_id=?", (checkout_id,))
            if c.fetchone():
                return {"status": "duplicate"}

            c.execute("INSERT INTO processed_payments (checkout_id) VALUES (?)", (checkout_id,))

            items = stk["CallbackMetadata"]["Item"]

            phone = None
            amount = None

            for i in items:
                if i["Name"] == "PhoneNumber":
                    phone = str(i["Value"])
                if i["Name"] == "Amount":
                    amount = float(i["Value"])

            update_balance(phone, amount)

            c.execute("""
                INSERT INTO transactions (sender, receiver, amount, type)
                VALUES (?, ?, ?, ?)
            """, (phone, "WALLET", amount, "MPESA"))

            conn.commit()
            conn.close()

        return {"ResultCode": 0}

    except:
        return {"ResultCode": 1}

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
