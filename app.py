from flask import Flask, request, session, redirect, jsonify
import sqlite3
import os
from time import time
from mpesa import Mpesa

app = Flask(__name__)
app.secret_key = "ute-secret-key"

# ================= ENV VARIABLES (PRODUCTION SAFE) =================
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

# ================= SECURITY STORAGE =================
last_request = {}

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect("ute.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        password TEXT,
        role TEXT,
        balance REAL DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        type TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS processed_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checkout_id TEXT UNIQUE
    )
    """)

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

# ================= RATE LIMIT =================
def rate_limit(user):
    now = time()

    if user in last_request:
        if now - last_request[user] < 10:
            return False

    last_request[user] = now
    return True

# ================= HOME =================
@app.route("/")
def home():
    return "<h1>UTE SECURE FINTECH SYSTEM</h1>"

# ================= CALLBACK (SECURE CORE) =================
@app.route("/callback", methods=["POST"])
def callback():

    if not request.is_json:
        return {"error": "invalid request"}, 403

    data = request.json

    try:
        stk = data["Body"]["stkCallback"]
    except:
        return {"error": "bad payload"}, 400

    if stk.get("ResultCode") != 0:
        return {"status": "failed"}

    checkout_id = stk.get("CheckoutRequestID")

    conn = sqlite3.connect("ute.db")
    c = conn.cursor()

    # ================= ANTI DUPLICATE =================
    c.execute("SELECT * FROM processed_payments WHERE checkout_id=?", (checkout_id,))
    if c.fetchone():
        return {"status": "duplicate ignored"}

    c.execute("INSERT INTO processed_payments (checkout_id) VALUES (?)", (checkout_id,))

    metadata = stk.get("CallbackMetadata", {}).get("Item", [])

    phone = None
    amount = None

    for item in metadata:
        if item["Name"] == "PhoneNumber":
            phone = str(item["Value"])
        if item["Name"] == "Amount":
            amount = float(item["Value"])

    # ================= VALIDATION =================
    if not phone or not amount or amount <= 0:
        return {"error": "invalid payment"}, 403

    # ================= CREDIT WALLET =================
    update_balance(phone, amount)

    c.execute("""
        INSERT INTO transactions (sender, receiver, amount, type)
        VALUES (?, ?, ?, ?)
    """, (phone, "WALLET", amount, "MPESA"))

    conn.commit()
    conn.close()

    return {"ResultCode": 0, "ResultDesc": "Accepted"}

# ================= STK PUSH =================
@app.route("/stk", methods=["POST"])
def stk():

    phone = request.form["phone"]
    amount = request.form["amount"]

    # ================= SECURITY CHECK =================
    if len(phone) < 10 or float(amount) <= 0:
        return {"error": "invalid input"}, 400

    if not rate_limit(phone):
        return {"error": "too many requests"}, 429

    res = mpesa.stk_push(
        phone,
        amount,
        "https://your-app.onrender.com/callback"
    )

    return jsonify(res)

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
