from flask import Flask, request, redirect, session, jsonify
from ute import UTE
from mpesa import Mpesa
from dotenv import load_dotenv
import os

# Load environment variables (for local dev)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "ute-default-key")

ute = UTE()
mpesa = Mpesa()

# ================= PREMIUM UI =================
STYLE = """
<style>
body {
    margin: 0;
    font-family: Arial;
    background: #0b1220;
    color: white;
}

.nav {
    background: #0f172a;
    padding: 18px;
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.card {
    background: #1f2937;
    margin: 12px auto;
    padding: 18px;
    border-radius: 14px;
    width: 90%;
    max-width: 750px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
}

input {
    width: 90%;
    padding: 10px;
    margin: 6px 0;
    border-radius: 10px;
    border: none;
    background: #0f172a;
    color: white;
}

button {
    padding: 12px 18px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #38bdf8, #2563eb);
    color: white;
    cursor: pointer;
    transition: 0.2s;
}

button:hover {
    transform: scale(1.03);
}

.logout {
    background: linear-gradient(135deg, #ef4444, #b91c1c);
}
</style>
"""

# ================= HEALTH CHECK =================
@app.route("/health")
def health():
    return {
        "status": "UP",
        "system": "UTE FINTECH",
        "wallet": True,
        "mpesa": True
    }

# ================= HOME =================
@app.route("/")
def home():
    return STYLE + """
    <div class="nav">
        <h3>UTE FINTECH</h3>
    </div>

    <div class="card">
        <h2>Welcome to UTE</h2>
        <a href="/auth"><button>Get Started</button></a>
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
        <h3>💸 Payroll / Transfer</h3>
        <form method="post" action="/pay">
            <input name="receiver" placeholder="Receiver"><br>
            <input name="amount" placeholder="Amount"><br>
            <button>Send</button>
        </form>
    </div>

    <div class="card">
        <h3>📲 M-Pesa Deposit</h3>
        <form method="post" action="/mpesa/stk">
            <input name="phone" placeholder="2547XXXXXXXX"><br>
            <input name="amount" placeholder="Amount"><br>
            <button>Pay with M-Pesa</button>
        </form>
    </div>

    <div class="card">
        <h3>📊 Transactions</h3>
        {tx_html}
    </div>
    """

# ================= PAYROLL =================
@app.route("/pay", methods=["POST"])
def pay():

    sender = session["user"]
    receiver = request.form["receiver"]
    amount = float(request.form["amount"])

    ute.process_salary(sender, receiver, amount)

    return redirect("/dashboard")

# ================= MPESA STK PUSH =================
@app.route("/mpesa/stk", methods=["POST"])
def stk():

    phone = request.form["phone"]
    amount = request.form["amount"]

    callback_url = os.getenv(
        "CALLBACK_URL",
        "https://your-app.onrender.com/mpesa/callback"
    )

    response = mpesa.stk_push(phone, amount, callback_url)

    return jsonify(response)

# ================= MPESA CALLBACK =================
@app.route("/mpesa/callback", methods=["POST"])
def callback():

    try:
        data = request.json
        stk = data["Body"]["stkCallback"]

        result_code = stk["ResultCode"]
        metadata = stk.get("CallbackMetadata", {}).get("Item", [])

        phone = None
        amount = None

        for item in metadata:
            if item["Name"] == "PhoneNumber":
                phone = item["Value"]
            if item["Name"] == "Amount":
                amount = item["Value"]

        if result_code == 0:
            ute.log_transaction(phone, "UTE SYSTEM", amount, "MPESA")

        return jsonify({"status": "ok"})

    except:
        return jsonify({"status": "failed"})

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
