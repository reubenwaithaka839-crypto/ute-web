from flask import Flask, request, jsonify, render_template_string, redirect, session
import sqlite3
import os
from mpesa import lipa_na_mpesa_online

app = Flask(__name__)
app.secret_key = "supersecretkey"

DATABASE = "ute.db"

# ------------------ DATABASE ------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        balance REAL DEFAULT 0
    )''')

    conn.commit()
    conn.close()

def get_balance(username):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("SELECT balance FROM users WHERE username=?", (username,))
    result = c.fetchone()

    conn.close()
    return result[0] if result else 0

def update_balance(username, amount):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    c.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, username))

    conn.commit()
    conn.close()

# ------------------ ROUTES ------------------

@app.route("/")
def home():
    return redirect("/auth")

# -------- AUTH --------
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()

        c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, COALESCE((SELECT balance FROM users WHERE username=?),0))",
                  (username, password, role, username))

        conn.commit()
        conn.close()

        session["user"] = username
        session["role"] = role

        return redirect("/dashboard")

    return render_template_string("""
    <h2>UTE FINTECH REGISTER</h2>
    <form method="POST">
        <input name="username" placeholder="Username" required><br><br>
        <input name="password" type="password" placeholder="Password" required><br><br>

        <select name="role">
            <option value="admin">Admin</option>
            <option value="employer">Employer</option>
            <option value="employee">Employee</option>
        </select><br><br>

        <button type="submit">Register / Login</button>
    </form>
    """)

# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/auth")

    user = session["user"]
    role = session["role"]
    balance = get_balance(user)

    return render_template_string(f"""
    <h1>UTE DASHBOARD</h1>
    <p>User: {user}</p>
    <p>Role: {role}</p>
    <p>Balance: KES {balance}</p>

    <h3>Actions</h3>
    <a href="/deposit">Deposit (M-Pesa)</a><br><br>
    <a href="/pay">Payroll Payment</a><br><br>
    <a href="/logout">Logout</a>
    """)

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")

# -------- DEPOSIT (M-PESA) --------
@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if request.method == "POST":
        phone = request.form["phone"]
        amount = int(request.form["amount"])

        response = lipa_na_mpesa_online(phone, amount)

        return jsonify(response)

    return render_template_string("""
    <h2>Deposit via M-Pesa</h2>
    <form method="POST">
        <input name="phone" placeholder="2547XXXXXXXX" required><br><br>
        <input name="amount" placeholder="Amount" required><br><br>
        <button type="submit">Pay</button>
    </form>
    """)

# -------- CALLBACK --------
@app.route("/callback", methods=["POST"])
def callback():
    data = request.json

    try:
        result = data["Body"]["stkCallback"]

        if result["ResultCode"] == 0:
            amount = result["CallbackMetadata"]["Item"][0]["Value"]
            phone = result["CallbackMetadata"]["Item"][4]["Value"]

            user = session.get("user")
            if user:
                update_balance(user, amount)

        return jsonify({"status": "success"})

    except:
        return jsonify({"error": "callback error"})

# -------- PAYROLL --------
@app.route("/pay", methods=["GET", "POST"])
def pay():
    if request.method == "POST":
        employee = request.form["employee"]
        amount = float(request.form["amount"])

        update_balance(employee, amount)

        return "Salary Paid!"

    return render_template_string("""
    <h2>Payroll</h2>
    <form method="POST">
        <input name="employee" placeholder="Employee Username"><br><br>
        <input name="amount" placeholder="Amount"><br><br>
        <button type="submit">Send Salary</button>
    </form>
    """)

# -------- HEALTH CHECK --------
@app.route("/health")
def health():
    return "OK"

# ------------------ RUN ------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
