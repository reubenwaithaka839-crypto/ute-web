from flask import Flask, request, redirect, session
from ute import UTE
import bcrypt

app = Flask(__name__)
app.secret_key = "UTE_FINAL_SYSTEM_KEY"

ute = UTE()

# ================= HOME =================
@app.route("/")
def home():
    return """
    <h1>UTE FINTECH SYSTEM</h1>
    <a href="/auth">Login / Register</a>
    """

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
        <input name="name" placeholder="Name"><br>
        <input name="password" type="password" placeholder="Password"><br>

        <select name="role">
            <option value="employee">Employee</option>
            <option value="employer">Employer</option>
            <option value="admin">Admin</option>
        </select><br>

        <button type="submit">Submit</button>
    </form>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/auth")

    user = session["user"]
    role = session["role"]
    balance = ute.get_balance(user)

    return f"""
    <h1>{role.upper()} DASHBOARD</h1>
    <h3>User: {user}</h3>
    <h3>Balance: {balance}</h3>

    <a href="/wallet">Wallet</a><br>
    <a href="/pay">Transfer</a><br>
    <a href="/set_salary">Set Salary</a><br>
    <a href="/payroll_dashboard">Payroll Dashboard</a><br>
    <a href="/fraud_dashboard">Fraud Dashboard</a><br>
    <a href="/transactions">Transactions</a><br>
    <a href="/compliance_report">Compliance Report</a><br>

    {"<a href='/admin'>Admin Panel</a><br>" if role == "admin" else ""}
    <a href="/logout">Logout</a>
    """

# ================= WALLET =================
@app.route("/wallet")
def wallet():
    user = session["user"]
    balance = ute.get_balance(user)
    return f"<h1>Wallet: {balance}</h1><a href='/dashboard'>Back</a>"

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
        employer = session["user"]
        employee = request.form["employee"]
        salary = float(request.form["salary"])

        ute.set_salary(employer, employee, salary)
        return redirect("/dashboard")

    return """
    <form method="POST">
        Employee: <input name="employee"><br>
        Salary: <input name="salary"><br>
        <button>Assign</button>
    </form>
    """

@app.route("/run_payroll")
def run_payroll():
    if session.get("role") != "admin":
        return "Access Denied"

    ute.run_payroll()
    return "Payroll Executed"

# ================= PAYROLL DASHBOARD =================
@app.route("/payroll_dashboard")
def payroll_dashboard():
    data = ute.get_all_payroll()
    total = ute.get_total_payroll_amount()

    rows = ""
    for e, emp, sal in data:
        rows += f"<tr><td>{e}</td><td>{emp}</td><td>{sal}</td></tr>"

    return f"""
    <h1>Payroll Dashboard</h1>
    <h3>Total: {total}</h3>
    <table border="1">
        <tr><th>Employer</th><th>Employee</th><th>Salary</th></tr>
        {rows}
    </table>
    """

# ================= FRAUD DASHBOARD =================
@app.route("/fraud_dashboard")
def fraud_dashboard():
    data = ute.get_fraud_logs()

    rows = ""
    for r in data:
        rows += f"<tr><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>"

    return f"""
    <h1>Fraud Dashboard</h1>
    <table border="1">
        <tr><th>User</th><th>Reason</th><th>Amount</th></tr>
        {rows}
    </table>
    """

# ================= TRANSACTIONS =================
@app.route("/transactions")
def transactions():
    data = ute.cursor.execute("SELECT * FROM mpesa_transactions").fetchall()

    rows = ""
    for r in data:
        rows += f"<tr><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td></tr>"

    return f"""
    <h1>Transactions</h1>
    <table border="1">
        <tr><th>Phone</th><th>Amount</th><th>Status</th></tr>
        {rows}
    </table>
    """

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "Access Denied"

    users = ute.get_total_users()
    balance = ute.get_total_system_balance()
    earnings = ute.get_admin_earnings()

    return f"""
    <h1>Admin Dashboard</h1>
    <p>Users: {users}</p>
    <p>System Balance: {balance}</p>
    <p>Earnings: {earnings}</p>
    <a href="/run_payroll">Run Payroll</a>
    """

# ================= COMPLIANCE =================
@app.route("/compliance_report")
def compliance():
    return f"""
    <h1>Compliance Report</h1>
    <p>Total Users: {ute.get_total_users()}</p>
    <p>Total Balance: {ute.get_total_system_balance()}</p>
    <p>Admin Earnings: {ute.get_admin_earnings()}</p>
    """

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
