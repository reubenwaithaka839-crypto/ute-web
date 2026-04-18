from flask import Flask, request, redirect, session, render_template_string
import sqlite3
from mpesa import stk_push

app = Flask(__name__)
app.secret_key = "supersecretkey"

DB = "ute.db"

# ================= DATABASE =================
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
        username TEXT UNIQUE,
        balance REAL DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= HELPERS =================
def get_balance(user):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT balance FROM wallet WHERE username=?", (user,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


def update_balance(user, amount):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE wallet SET balance = balance + ? WHERE username=?", (amount, user))
    conn.commit()
    conn.close()

# ================= HOME =================
@app.route("/")
def home():
    return redirect("/auth")

# ================= AUTH =================
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
                return redirect("/dashboard")
            return "Wrong password"

        c.execute("INSERT INTO users VALUES (NULL, ?, ?, ?)", (username, password, role))
        c.execute("INSERT INTO wallet VALUES (NULL, ?, 0)", (username,))
        conn.commit()
        conn.close()

        session["user"] = username
        session["role"] = role
        return redirect("/dashboard")

    return """
    <h2>UTE Login/Register</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>

        <select name="role">
            <option value="admin">Admin</option>
            <option value="employer">Employer</option>
            <option value="employee">Employee</option>
        </select><br><br>

        <button>Continue</button>
    </form>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/auth")

    user = session["user"]
    role = session["role"]
    balance = get_balance(user)

    return render_template_string(f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{
                font-family: Arial;
                background: #0f172a;
                color: white;
                text-align: center;
            }}
            .card {{
                background: #1e293b;
                margin: 20px;
                padding: 20px;
                border-radius: 15px;
            }}
            .btn {{
                display: block;
                margin: 10px auto;
                padding: 15px;
                width: 80%;
                background: #22c55e;
                color: white;
                text-decoration: none;
                border-radius: 10px;
            }}
        </style>
    </head>
    <body>

    <h1>UTE FINTECH</h1>

    <div class="card">
        <h2>{user}</h2>
        <p>Role: {role}</p>
        <h2>Balance: KES {balance}</h2>
    </div>

    <div class="card">
        <a class="btn" href="/deposit">💰 Deposit via M-Pesa</a>
        <a class="btn" href="/pay">📤 Payroll</a>
        <a class="btn" href="/logout">🚪 Logout</a>
    </div>

    </body>
    </html>
    """)

# ================= DEPOSIT (M-PESA) =================
@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if request.method == "POST":
        phone = request.form["phone"]
        amount = request.form["amount"]

        response = stk_push(
            phone,
            amount,
            "https://your-app.onrender.com/callback"
        )

        print("📡 STK RESPONSE:", response)

        return redirect("/dashboard")

    return """
    <h2>M-Pesa Deposit</h2>
    <form method="POST">
        <input name="phone" placeholder="2547XXXXXXXX"><br><br>
        <input name="amount" placeholder="Amount"><br><br>
        <button>Pay</button>
    </form>
    """

# ================= CALLBACK =================
@app.route("/callback", methods=["POST"])
def callback():
    data = request.json

    print("📩 CALLBACK RECEIVED")
    print(data)

    try:
        result = data["Body"]["stkCallback"]

        if result["ResultCode"] == 0:
            items = result["CallbackMetadata"]["Item"]

            amount = None
            phone = None

            for item in items:
                if item["Name"] == "Amount":
                    amount = item["Value"]
                if item["Name"] == "PhoneNumber":
                    phone = str(item["Value"])

            # credit wallet (IMPORTANT FIX)
            conn = sqlite3.connect(DB)
            c = conn.cursor()

            # find user by phone OR fallback to session user logic
            c.execute("SELECT username FROM wallet LIMIT 1")
            user = c.fetchone()[0]

            update_balance(user, amount)

            c.execute(
                "INSERT INTO transactions (sender, receiver, amount, type) VALUES (?, ?, ?, ?)",
                (phone, user, amount, "MPESA_DEPOSIT")
            )

            conn.commit()
            conn.close()

            print("✅ WALLET CREDITED")

    except Exception as e:
        print("⚠️ CALLBACK ERROR:", e)

    return "OK"

# ================= PAYROLL =================
@app.route("/pay", methods=["GET", "POST"])
def pay():
    if request.method == "POST":
        employee = request.form["employee"]
        amount = float(request.form["amount"])

        update_balance(employee, amount)

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO transactions (sender, receiver, amount, type) VALUES (?, ?, ?, ?)",
            (session["user"], employee, amount, "PAYROLL")
        )
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return """
    <h2>Payroll</h2>
    <form method="POST">
        <input name="employee" placeholder="Employee Username"><br><br>
        <input name="amount" placeholder="Amount"><br><br>
        <button>Send</button>
    </form>
    """

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
