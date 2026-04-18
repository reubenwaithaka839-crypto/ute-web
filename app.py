from flask import Flask, request, session, redirect, jsonify
import sqlite3
import os
import time
import numpy as np
import joblib
from mpesa import Mpesa

app = Flask(__name__)
app.secret_key = "ute-secret-key"

# ================= M-PESA CONFIG =================
mpesa = Mpesa(
    os.environ.get("MPESA_KEY"),
    os.environ.get("MPESA_SECRET"),
    os.environ.get("MPESA_SHORTCODE"),
    os.environ.get("MPESA_PASSKEY"),
    "https://sandbox.safaricom.co.ke"
)

# ================= LOAD AI MODEL =================
fraud_model = joblib.load("fraud_model.pkl")

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

# ================= AI FRAUD SYSTEM =================
def fraud_check(amount):
    hour = int(time.strftime("%H"))
    features = np.array([[amount, 2, hour]])  # simplified model input
    return fraud_model.predict(features)[0]

# ================= HOME =================
@app.route("/")
def home():
    return "<h1>UTE FINTECH SYSTEM</h1>"

# ================= AUTH =================
@app.route("/auth", methods=["GET", "POST"])
def auth():

    if request.method == "POST":

        name = request.form["name"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("ute.db")
        c = conn.cursor()

        c.execute("INSERT INTO users VALUES (NULL, ?, ?, ?, ?)",
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
        <button>Create Account</button>
    </form>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    user = session.get("user")
    role = session.get("role")

    return f"""
    <h2>{user} ({role})</h2>
    <h3>Balance: {get_balance(user)}</h3>
    <a href="/payroll">Payroll</a><br>
    <a href="/stk">Deposit</a>
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

        c.execute("INSERT INTO payroll VALUES (NULL, ?, ?, ?, ?)",
                  (employer, employee, amount, "PAID"))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return """
    <form method="post">
        <input name="employee">
        <input name="amount">
        <button>Pay</button>
    </form>
    """

# ================= STK PUSH + AI FRAUD =================
@app.route("/stk", methods=["POST"])
def stk():

    phone = request.form["phone"]
    amount = float(request.form["amount"])

    if not rate_limit(phone):
        return {"error": "Too many requests"}, 429

    # AI FRAUD CHECK
    if fraud_check(amount) == 1:
        return {"status": "blocked", "reason": "fraud detected"}

    return jsonify(mpesa.stk_push(
        phone,
        amount,
        "https://your-app.onrender.com/callback"
    ))

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

            c.execute("INSERT INTO processed_payments VALUES (NULL, ?)", (checkout_id,))

            items = stk["CallbackMetadata"]["Item"]

            phone = None
            amount = None

            for i in items:
                if i["Name"] == "PhoneNumber":
                    phone = str(i["Value"])
                if i["Name"] == "Amount":
                    amount = float(i["Value"])

            update_balance(phone, amount)

            c.execute("INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?)",
                      (phone, "WALLET", amount, "MPESA"))

            conn.commit()
            conn.close()

        return {"ResultCode": 0}

    except:
        return {"ResultCode": 1}

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
