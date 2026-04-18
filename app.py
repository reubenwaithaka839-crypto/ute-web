from flask import Flask, request, redirect, session
from ute import UTE
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ute-secret-key")

ute = UTE()

# ================= STYLE (STRIPE-LIKE UI) =================
STYLE = """
<style>
body {
    margin: 0;
    font-family: Arial;
    background: #0b1220;
    color: white;
}

.nav {
    background: #111827;
    padding: 15px;
    display: flex;
    justify-content: space-between;
}

.card {
    background: #1f2937;
    margin: 10px;
    padding: 15px;
    border-radius: 12px;
}

button {
    background: #38bdf8;
    border: none;
    padding: 10px;
    border-radius: 6px;
    cursor: pointer;
}

input {
    padding: 8px;
    margin: 5px;
    width: 80%;
}
</style>
"""

# ================= HOME =================
@app.route("/")
def home():
    return STYLE + """
    <div class="nav">
        <h3>UTE FINTECH SYSTEM</h3>
    </div>

    <div class="card">
        <h2>Welcome to UTE</h2>
        <a href="/auth"><button>Login / Register</button></a>
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
            <button>Login</button>
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
        for t in tx[:5]
    ])

    return STYLE + f"""
    <div class="nav">
        <h3>Dashboard</h3>
        <a href="/logout">Logout</a>
    </div>

    <div class="card">
        <h2>Balance: KES {balance}</h2>
    </div>

    <div class="card">
        <h3>Send Money (Payroll / Transfer)</h3>
        <form method="post" action="/pay">
            <input name="receiver" placeholder="Receiver"><br>
            <input name="amount" placeholder="Amount"><br>
            <button>Send</button>
        </form>
    </div>

    <div class="card">
        <h3>Recent Transactions</h3>
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
