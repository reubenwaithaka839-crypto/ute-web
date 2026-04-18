from flask import Flask, request, redirect, session, jsonify
import sqlite3
from mpesa import Mpesa

app = Flask(__name__)
app.secret_key = "ute-secret-key"

# ================= INIT M-PESA =================
mpesa = Mpesa(
    consumer_key="YOUR_KEY",
    consumer_secret="YOUR_SECRET",
    shortcode="174379",
    passkey="YOUR_PASSKEY",
    base_url="https://sandbox.safaricom.co.ke"
)

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

    conn.commit()
    conn.close()

init_db()

# ================= STYLE =================
STYLE = """
<style>
body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI";
    background: #0a0f1c;
    color: white;
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
        <h2>UTE FINTECH SYSTEM</h2>
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

# ================= WALLET =================
def get_balance(user):
    conn = sqlite3.connect("ute.db")
    c = conn.cursor()

    c.execute("SELECT balance FROM users WHERE name=?", (user,))
    data = c.fetchone()

    conn.close()
    return data[0] if data else 0


def update_balance(user, amount):
    conn = sqlite3.connect("ute.db")
    c = conn.cursor()

    c.execute("UPDATE users SET balance = balance + ? WHERE name=?",
              (amount, user))

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
        <h3>💳 M-Pesa Deposit</h3>

        <form method="post" action="/stk">
            <input name="phone" placeholder="2547XXXXXXXX">
            <input name="amount" placeholder="Amount">
            <button>Send STK Push</button>
        </form>
    </div>
    """

# ================= STK PUSH =================
@app.route("/stk", methods=["POST"])
def stk():

    phone = request.form["phone"]
    amount = request.form["amount"]

    response = mpesa.stk_push(
        phone,
        amount,
        "https://your-app.onrender.com/callback"
    )

    return jsonify(response)

# ================= CALLBACK =================
@app.route("/callback", methods=["POST"])
def callback():

    data = request.json

    try:
        stk = data["Body"]["stkCallback"]

        if stk["ResultCode"] == 0:

            metadata = stk["CallbackMetadata"]["Item"]

            phone = None
            amount = None

            for item in metadata:
                if item["Name"] == "PhoneNumber":
                    phone = str(item["Value"])
                if item["Name"] == "Amount":
                    amount = float(item["Value"])

            update_balance(phone, amount)

            conn = sqlite3.connect("ute.db")
            c = conn.cursor()

            c.execute("""
                INSERT INTO transactions (sender, receiver, amount, type)
                VALUES (?, ?, ?, ?)
            """, (phone, "WALLET", amount, "MPESA"))

            conn.commit()
            conn.close()

        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    except:
        return {"ResultCode": 1, "ResultDesc": "Failed"}

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
