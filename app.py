import os
from flask import Flask, request, redirect, session
from ute import UTE

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ute-secure-default-key")

ute = UTE()

# =========================
# 🎨 PREMIUM UI STYLE
# =========================
STYLE = """
<style>
body {
    margin: 0;
    font-family: 'Segoe UI', sans-serif;
    background: radial-gradient(circle at top, #0f172a, #020617);
    color: white;
}

.sidebar {
    width: 250px;
    height: 100vh;
    position: fixed;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(15px);
    padding: 20px;
}

.sidebar h2 {
    color: #38bdf8;
}

.sidebar a {
    display: block;
    margin: 15px 0;
    color: #cbd5f5;
    text-decoration: none;
}

.sidebar a:hover {
    color: #38bdf8;
}

.main {
    margin-left: 270px;
    padding: 30px;
}

.card {
    background: rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 0 25px rgba(0,0,0,0.5);
}

button {
    padding: 12px 18px;
    border: none;
    border-radius: 10px;
    background: linear-gradient(45deg,#38bdf8,#6366f1);
    color: white;
    cursor: pointer;
}

input {
    padding: 12px;
    width: 100%;
    margin-bottom: 10px;
    border-radius: 8px;
    border: none;
}

.center {
    text-align: center;
    margin-top: 120px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 15px;
}
</style>
"""

# =========================
# 🌍 HOME
# =========================
@app.route("/")
def home():
    return STYLE + """
    <div class="center">
        <h1>🌍 Welcome to UTE Platform</h1>
        <p>Work • Payroll • Jobs • Finance • Future System</p>

        <a href="/auth?role=company"><button>🏢 Organization</button></a>
        <a href="/auth?role=worker"><button>👷 Job Seeker</button></a>
        <a href="/auth?role=admin"><button>🔐 Admin Panel</button></a>
    </div>
    """

# =========================
# 📜 TERMS
# =========================
@app.route("/terms")
def terms():
    return STYLE + """
    <div class="main">
        <h1>📜 Terms & Conditions</h1>
        <div class="card">
            <ul>
                <li>30% first salary deduction</li>
                <li>10% monthly processing fee</li>
                <li>2% platform fee</li>
                <li>All data is stored securely</li>
            </ul>
        </div>
    </div>
    """

# =========================
# 🔐 AUTH
# =========================
@app.route("/auth", methods=["GET", "POST"])
def auth():
    role = request.args.get("role")

    if request.method == "POST":

        if "agree" not in request.form:
            return STYLE + """
            <div class="center">
                <h2>❌ Accept Terms & Conditions First</h2>
                <a href="/">Go Back</a>
            </div>
            """

        name = request.form["name"]
        password = request.form["password"]

        ute.register_company(name, password)
        login = ute.login_company(name, password)

        if login:
            session["user"] = name
            session["role"] = role

            if role == "admin":
                session["admin"] = True
                return redirect("/admin")

            return redirect(f"/{role}")

    return STYLE + f"""
    <div class="center">
        <h2>{role.upper()} LOGIN</h2>

        <form method="post">
            <input name="name" placeholder="Username" required>
            <input name="password" type="password" placeholder="Password" required>

            <div style="text-align:left; margin:10px;">
                <input type="checkbox" name="agree">
                I agree to <a href="/terms" target="_blank">Terms</a>
            </div>

            <button>Continue</button>
        </form>
    </div>
    """

# =========================
# 🏢 COMPANY DASHBOARD
# =========================
@app.route("/company")
def company():
    if session.get("role") != "company":
        return redirect("/")

    employees = ute.get_company_employees(session["user"])

    emp_html = "".join([
        f"<p>👤 {e[0]} — {e[1]} months</p>"
        for e in employees
    ])

    return STYLE + f"""
    <div class="sidebar">
        <h2>UTE</h2>
        <a href="#">📊 Dashboard</a>
        <a href="/logout">🚪 Logout</a>
    </div>

    <div class="main">
        <h1>🏢 Company Dashboard</h1>

        <div class="grid">
            <div class="card">
                <h3>👥 Employees</h3>
                <h2>{len(employees)}</h2>
            </div>

            <div class="card">
                <h3>💰 Payroll System</h3>
                <p>Active</p>
            </div>
        </div>

        <div class="card">
            <h3>💰 Process Salary</h3>
            <form method="post" action="/process">
                <input name="employee" placeholder="Employee Name" required>
                <input name="salary" placeholder="Salary Amount" required>
                <button>Process</button>
            </form>
        </div>

        <div class="card">
            <h3>📋 Employees</h3>
            {emp_html if emp_html else "No employees"}
        </div>
    </div>
    """

# =========================
# 💰 PROCESS SALARY
# =========================
@app.route("/process", methods=["POST"])
def process():
    ute.process_salary(
        session["user"],
        request.form["employee"],
        request.form["salary"],
        False
    )
    return redirect("/company")

# =========================
# 👷 WORKER DASHBOARD
# =========================
@app.route("/worker")
def worker():
    jobs = ute.get_jobs()

    jobs_html = "".join([
        f"""
        <div class="card">
            <h3>{j['title']}</h3>
            <p>📍 {j['location']}</p>
            <p>💰 KES {j['salary']}</p>
            <button>Apply</button>
        </div>
        """
        for j in jobs
    ])

    return STYLE + f"""
    <div class="sidebar">
        <h2>UTE</h2>
        <a href="#">💼 Jobs</a>
        <a href="/logout">🚪 Logout</a>
    </div>

    <div class="main">
        <h1>👷 Job Marketplace</h1>

        <div class="grid">
            {jobs_html}
        </div>
    </div>
    """

# =========================
# 🔐 ADMIN DASHBOARD
# =========================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("admin"):
        return redirect("/")

    if request.method == "POST":
        ute.save_bank_details(
            request.form["bank_name"],
            request.form["account_name"],
            request.form["account_number"]
        )

    transactions = ute.get_transactions()
    bank = ute.get_bank_details()

    tx_html = "".join([
        f"<p>🏢 {t[0]} → 👤 {t[1]} | 💰 +{t[2]}</p>"
        for t in transactions
    ])

    bank_html = ""
    if bank:
        bank_html = f"""
        <p><b>Bank:</b> {bank[0]}</p>
        <p><b>Account:</b> {bank[1]}</p>
        <p><b>Number:</b> {bank[2]}</p>
        """

    return STYLE + f"""
    <div class="sidebar">
        <h2>ADMIN</h2>
        <a href="#">📊 Dashboard</a>
        <a href="/logout">🚪 Logout</a>
    </div>

    <div class="main">
        <h1>🔐 Admin Panel</h1>

        <div class="grid">
            <div class="card">
                <h3>💰 Revenue</h3>
                <h2>KES {ute.get_revenue()}</h2>
            </div>

            <div class="card">
                <h3>🏢 Companies</h3>
                <h2>{ute.get_total_companies()}</h2>
            </div>

            <div class="card">
                <h3>👷 Workers</h3>
                <h2>{ute.get_total_workers()}</h2>
            </div>
        </div>

        <div class="card">
            <h3>🏦 Bank Setup</h3>
            <form method="post">
                <input name="bank_name" placeholder="Bank Name" required>
                <input name="account_name" placeholder="Account Name" required>
                <input name="account_number" placeholder="Account Number" required>
                <button>Save</button>
            </form>
            <br>
            {bank_html if bank else "No bank details"}
        </div>

        <div class="card">
            <h3>📄 Transactions</h3>
            {tx_html if tx_html else "No transactions"}
        </div>
    </div>
    """

# =========================
# 🚪 LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)