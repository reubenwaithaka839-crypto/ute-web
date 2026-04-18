from flask import Flask, request, redirect, session, render_template_string
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB = "ute.db"

# -----------------------------
# DATABASE INIT
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS wallet (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        balance REAL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()
    print("✅ DB INITIALIZED")

init_db()

# -----------------------------
# HELPERS
# -----------------------------
def get_balance(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT balance FROM wallet WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def update_balance(username, amount):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE wallet SET balance = balance + ? WHERE username=?", (amount, username))
    conn.commit()
    conn.close()
    print(f"💰 BALANCE UPDATED → {username}: +{amount}")

# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    print("🏠 HOME LOADED")
    return """
    <h1>UTE FINTECH SYSTEM</h1>
    <a href="/auth">Enter System</a>
    """

# -----------------------------
# AUTH
# -----------------------------
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user:
            if user[2] == password:
                session["user"] = username
                session["role"] = user[3]
                print(f"✅ LOGIN SUCCESS → {username}")
                return redirect("/dashboard")
            else:
                print("❌ WRONG PASSWORD")
                return "Wrong password"
        else:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, password, role))
            c.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (username,))
            conn.commit()
            conn.close()

            print(f"🆕 USER CREATED → {username} ({role})")

            session["user"] = username
            session["role"] = role
            return redirect("/dashboard")

    return """
    <h2>Register / Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>

        <select name="role">
            <option value="admin">Admin</option>
            <option value="employer">Employer</option>
            <option value="employee">Employee</option>
        </select><br><br>

        <button type="submit">Continue</button>
    </form>
    """

# -----------------------------
# DASHBOARD (PREMIUM UI)
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        print("⚠️ NO SESSION")
        return redirect("/auth")

    user = session["user"]
    role = session["role"]
    balance = get_balance(user)

    print(f"📊 DASHBOARD → {user}")

    return render_template_string(f"""
    <html>
    <head>
        <title>UTE Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">

        <style>
            body {{
                margin: 0;
                font-family: 'Segoe UI', sans-serif;
                background: #0b1120;
                color: white;
            }}

            .header {{
                padding: 20px;
                background: linear-gradient(90deg, #0ea5e9, #22c55e);
                text-align: center;
                font-size: 24px;
                font-weight: bold;
            }}

            .container {{
                padding: 20px;
            }}

            .card {{
                background: #111827;
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}

            .balance {{
                font-size: 30px;
                color: #22c55e;
                font-weight: bold;
            }}

            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }}

            .btn {{
                padding: 20px;
                border-radius: 14px;
                text-align: center;
                text-decoration: none;
                color: white;
                font-weight: bold;
                font-size: 16px;
            }}

            .deposit {{ background: #22c55e; }}
            .pay {{ background: #3b82f6; }}
            .logout {{ background: #ef4444; }}
            .admin {{ background: #f59e0b; }}

        </style>
    </head>

    <body>

        <div class="header">💼 UTE FINTECH</div>

        <div class="container">

            <div class="card">
                <h2>{user}</h2>
                <p>Role: {role}</p>
                <div class="balance">KES {balance}</div>
            </div>

            <div class="card">
                <h3>⚡ Actions</h3>

                <div class="grid">
                    <a class="btn deposit" href="/deposit">💰 Deposit</a>
                    <a class="btn pay" href="/pay">📤 Pay</a>
                    {"<a class='btn admin' href='/admin'>🛠 Admin</a>" if role == "admin" else ""}
                    <a class="btn logout" href="/logout">🚪 Logout</a>
                </div>

            </div>

        </div>

    </body>
    </html>
    """)

# -----------------------------
# DEPOSIT
# -----------------------------
@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if request.method == "POST":
        amount = float(request.form["amount"])
        user = session["user"]

        print(f"📲 DEPOSIT REQUEST → {user}: {amount}")

        update_balance(user, amount)

        print("✅ DEPOSIT SUCCESS")
        return redirect("/dashboard")

    return """
    <h2>Deposit</h2>
    <form method="POST">
        <input name="amount" placeholder="Amount"><br><br>
        <button>Deposit</button>
    </form>
    """

# -----------------------------
# PAYROLL
# -----------------------------
@app.route("/pay", methods=["GET", "POST"])
def pay():
    if request.method == "POST":
        employee = request.form["employee"]
        amount = float(request.form["amount"])

        print(f"💼 PAYROLL → {employee}: {amount}")

        update_balance(employee, amount)

        return redirect("/dashboard")

    return """
    <h2>Send Salary</h2>
    <form method="POST">
        <input name="employee" placeholder="Employee Username"><br><br>
        <input name="amount" placeholder="Amount"><br><br>
        <button>Send</button>
    </form>
    """

# -----------------------------
# ADMIN PANEL
# -----------------------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "Access denied"

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT username, role FROM users")
    users = c.fetchall()
    conn.close()

    print("🛠 ADMIN PANEL LOADED")

    user_list = "<br>".join([f"{u[0]} ({u[1]})" for u in users])

    return f"<h2>All Users</h2>{user_list}<br><br><a href='/dashboard'>Back</a>"

# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    print("🚪 LOGOUT")
    return redirect("/")

# -----------------------------
# HEALTH CHECK
# -----------------------------
@app.route("/health")
def health():
    return "OK"

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    print("🚀 UTE STARTED")
    app.run(debug=True)
