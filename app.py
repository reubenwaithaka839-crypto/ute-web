from flask import Flask, request, session, redirect
from ute import UTE
import bcrypt

app = Flask(__name__)
app.secret_key = "UTE_FINAL_KEY"

ute = UTE()

# ================= HOME =================
@app.route("/")
def home():
    return "<h1>UTE FINTECH SYSTEM</h1><a href='/auth'>Start</a>"

# ================= AUTH =================
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]
        role = request.form["role"]

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        ute.register_user(name, hashed, role)
        ute.init_wallet(name)

        session["user"] = name
        session["role"] = role

        return redirect("/dashboard")

    return """
    <form method="POST">
        <input name="name"><br>
        <input name="password" type="password"><br>
        <select name="role">
            <option>employee</option>
            <option>employer</option>
            <option>admin</option>
        </select><br>
        <button>Submit</button>
    </form>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    user = session["user"]
    role = session["role"]
    bal = ute.get_balance(user)

    return f"""
    <h1>{role} DASHBOARD</h1>
    <p>User: {user}</p>
    <p>Balance: {bal}</p>

    <a href="/wallet">Wallet</a><br>
    <a href="/pay">Transfer</a><br>
    <a href="/set_salary">Payroll</a><br>
    <a href="/admin">Admin</a><br>
    """

# ================= WALLET =================
@app.route("/wallet")
def wallet():
    user = session["user"]
    return f"<h1>Balance: {ute.get_balance(user)}</h1>"

# ================= TRANSFER =================
@app.route("/pay", methods=["GET", "POST"])
def pay():
    if request.method == "POST":
        sender = session["user"]
        receiver = request.form["receiver"]
        amount = float(request.form["amount"])

        ute.transfer_with_commission(sender, receiver, amount)
        return redirect("/dashboard")

    return """
    <form method="POST">
        Receiver: <input name="receiver"><br>
        Amount: <input name="amount"><br>
        <button>Send</button>
    </form>
    """

# ================= PAYROLL =================
@app.route("/set_salary", methods=["GET", "POST"])
def set_salary():
    if request.method == "POST":
        ute.set_salary(
            session["user"],
            request.form["employee"],
            float(request.form["salary"])
        )
        return redirect("/dashboard")

    return """
    <form method="POST">
        Employee: <input name="employee"><br>
        Salary: <input name="salary"><br>
        <button>Set</button>
    </form>
    """

@app.route("/run_payroll")
def run_payroll():
    if session["role"] != "admin":
        return "Denied"

    ute.run_payroll()
    return "Payroll Done"

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if session["role"] != "admin":
        return "Denied"

    return f"""
    <h1>ADMIN</h1>
    <p>Users: {ute.get_total_users()}</p>
    <p>Balance: {ute.get_total_system_balance()}</p>
    <p>Earnings: {ute.get_admin_earnings()}</p>
    <a href="/run_payroll">Run Payroll</a>
    """

# ================= FRAUD =================
@app.route("/fraud")
def fraud():
    data = ute.get_fraud_logs()
    return "<br>".join(str(x) for x in data)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
