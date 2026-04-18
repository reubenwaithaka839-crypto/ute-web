from flask import Flask, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "ute-secret-key"

# ================= DATABASE SETUP =================
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

    conn.commit()
    conn.close()

init_db()

# ================= STYLE =================
STYLE = """
<style>
body {
    font-family: Arial;
    background: #0a0f1c;
    color: white;
    margin: 0;
}

.card {
    background: #111827;
    margin: 15px auto;
    padding: 20px;
    width: 90%;
    max-width: 700px;
    border-radius: 14px;
}

input, select {
    width: 100%;
    padding: 12px;
    margin: 6px 0;
    border-radius: 10px;
}

button {
    width: 100%;
    padding: 14px;
    background: #4f46e5;
    color: white;
    border: none;
    border-radius: 10px;
}
</style>
"""

# ================= HOME =================
@app.route("/")
def home():
    return STYLE + """
    <div class="card">
        <h2>UTE FINTECH</h2>
        <a href="/auth"><button>Register / Login</button></a>
    </div>
    """

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

    return STYLE + """
    <div class="card">
        <h2>Create Account</h2>

        <form method="post">
            <input name="name" placeholder="Name">
            <input name="password" type="password" placeholder="Password">

            <select name="role">
                <option value="admin">Admin</option>
                <option value="employer">Employer</option>
                <option value="employee">Employee</option>
            </select>

            <button>Create</button>
        </form>
    </div>
    """

# ================= GET BALANCE =================
def get_balance(user):
    conn = sqlite3.connect("ute.db")
    c = conn.cursor()

    c.execute("SELECT balance FROM users WHERE name=?", (user,))
    result = c.fetchone()

    conn.close()

    return result[0] if result else 0

# ================= UPDATE BALANCE =================
def update_balance(user, amount):
    conn = sqlite3.connect("ute.db")
    c = conn.cursor()

    c.execute("UPDATE users SET balance = balance + ? WHERE name=?", (amount, user))

    conn.commit()
    conn.close()

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    user = session.get("user")
    role = session.get("role")

    if not user:
        return redirect("/auth")

    balance = get_balance(user)

    return STYLE + f"""
    <div class="card">
        <h2>Welcome {user}</h2>
        <h3>Role: {role}</h3>
        <h2>💰 Balance: KES {balance}</h2>
    </div>

    <div class="card">
        <h3>Deposit (Simulated)</h3>

        <form method="post" action="/deposit">
            <input name="amount" placeholder="Amount">
            <button>Deposit</button>
        </form>
    </div>

    <div class="card">
        <h3>Transfer</h3>

        <form method="post" action="/transfer">
            <input name="receiver" placeholder="Receiver">
            <input name="amount" placeholder="Amount">
            <button>Send</button>
        </form>
    </div>
    """

# ================= DEPOSIT =================
@app.route("/deposit", methods=["POST"])
def deposit():

    user = session["user"]
    amount = float(request.form["amount"])

    update_balance(user, amount)

    return redirect("/dashboard")

# ================= TRANSFER =================
@app.route("/transfer", methods=["POST"])
def transfer():

    sender = session["user"]
    receiver = request.form["receiver"]
    amount = float(request.form["amount"])

    conn = sqlite3.connect("ute.db")
    c = conn.cursor()

    c.execute("SELECT balance FROM users WHERE name=?", (sender,))
    sender_balance = c.fetchone()[0]

    if sender_balance >= amount:

        c.execute("UPDATE users SET balance = balance - ? WHERE name=?", (amount, sender))
        c.execute("UPDATE users SET balance = balance + ? WHERE name=?", (amount, receiver))

        c.execute("INSERT INTO transactions (sender, receiver, amount, type) VALUES (?, ?, ?, ?)",
                  (sender, receiver, amount, "TRANSFER"))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
