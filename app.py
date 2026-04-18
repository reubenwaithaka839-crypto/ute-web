from flask import Flask, request, redirect, session
from ute import UTE
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ute-secret-key")

ute = UTE()

# ================= PREMIUM UI STYLE =================
STYLE = """
<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #0b1220;
    color: white;
}

/* NAVBAR */
.nav {
    background: #0f172a;
    padding: 18px 25px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

/* CARDS */
.card {
    background: linear-gradient(145deg, #111827, #0f172a);
    margin: 15px auto;
    padding: 20px;
    border-radius: 16px;
    width: 90%;
    max-width: 750px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
}

/* INPUTS */
input {
    width: 90%;
    padding: 12px;
    margin: 8px 0;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.1);
    background: #0f172a;
    color: white;
    outline: none;
}

/* ================= PREMIUM BUTTONS ================= */
button {
    padding: 12px 20px;
    border: none;
    border-radius: 12px;
    cursor: pointer;

    font-weight: 600;
    letter-spacing: 0.5px;

    transition: all 0.25s ease;
    background: linear-gradient(135deg, #38bdf8, #2563eb);
    color: white;

    box-shadow: 0 6px 18px rgba(56,189,248,0.25);
}

button:hover {
    transform: translateY(-3px) scale(1.03);
    box-shadow: 0 10px 25px rgba(56,189,248,0.4);
}

button:active {
    transform: translateY(1px) scale(0.98);
}

/* GREEN BUTTON (LOGIN / ACTION) */
.green {
    background: linear-gradient(135deg, #22c55e, #16a34a);
    box-shadow: 0 6px 18px rgba(34,197,94,0.25);
}

/* RED BUTTON (LOGOUT) */
.logout {
    background: linear-gradient(135deg, #ef4444, #b91c1c);
    box-shadow: 0 6px 18px rgba(239,68,68,0.25);
}

/* CENTER */
.center {
    text-align: center;
    margin-top: 80px;
}
</style>
"""

# ================= HOME =================
@app.route("/")
def home():
    return STYLE + """
    <div class="nav">
        <h3>UTE FINTECH</h3>
    </div>

    <div class="center">
        <h1>Welcome to UTE System</h1>
        <a href="/auth"><button>🚀 Get Started</button></a>
    </div>
    """

# ================= AUTH =================
@app.route("/auth", methods=["GET", "POST"])
def auth():

    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]

        ute.register_company(name, password)

        session["user"] = name

        return redirect("/dashboard")

    return STYLE + """
    <div class="card">
        <h2>Login</h2>
        <form method="post">
            <input name="name" placeholder="Name"><br>
            <input name="password" type="password" placeholder="Password"><br>
            <button class="green">Login</button>
        </form>
    </div>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    user = session.get("user")

    if not user:
        return redirect("/auth")

    balance = ute.get_balance(user)
    tx = ute.get_transactions()

    tx_html = "".join([
        f"<div class='card'>{t[0]} → {t[1]} | KES {t[2]} | {t[3]}</div>"
        for t in tx[:6]
    ])

    return STYLE + f"""
    <div class="nav">
        <h3>Dashboard</h3>
        <a href="/logout"><button class="logout">Logout</button></a>
    </div>

    <div class="card">
        <h2>💰 Balance: KES {balance}</h2>
    </div>

    <div class="card">
        <h3>💸 Send Money / Payroll</h3>
        <form method="post" action="/pay">
            <input name="receiver" placeholder="Receiver"><br>
            <input name="amount" placeholder="Amount"><br>
            <button>Send Payment</button>
        </form>
    </div>

    <div class="card">
        <h3>📊 Recent Transactions</h3>
        {tx_html}
    </div>
    """

# ================= PAYMENT =================
@app.route("/pay", methods=["POST"])
def pay():

    sender = session.get("user")
    receiver = request.form["receiver"]
    amount = float(request.form["amount"])

    ute.process_salary(sender, receiver, amount)

    return redirect("/dashboard")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
