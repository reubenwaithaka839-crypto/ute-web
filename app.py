from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "ute-secret-key"

# ================= TEMP STORAGE =================
users = {}

# ================= STRIPE STYLE UI =================
STYLE = """
<style>
body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
    background: #0a0f1c;
    color: white;
}

.nav {
    background: #0f172a;
    padding: 18px;
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}

.container {
    max-width: 900px;
    margin: auto;
    padding: 20px;
}

.card {
    background: #111827;
    padding: 20px;
    border-radius: 16px;
    margin: 15px 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
}

input, select {
    width: 100%;
    padding: 14px;
    margin: 8px 0;
    border-radius: 12px;
    border: none;
    background: #0f172a;
    color: white;
    font-size: 15px;
}

button {
    width: 100%;
    padding: 14px;
    margin-top: 10px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #635bff, #4f46e5);
    color: white;
    font-size: 16px;
    cursor: pointer;
    transition: 0.2s;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(99,91,255,0.3);
}

.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    background: #1f2937;
    font-size: 12px;
}
</style>
"""

# ================= HOME =================
@app.route("/")
def home():
    return STYLE + """
    <div class="container">
        <h1>🚀 UTE FINTECH SYSTEM</h1>
        <div class="card">
            <p>Next-generation payment & payroll platform</p>
            <a href="/auth"><button>Get Started</button></a>
        </div>
    </div>
    """

# ================= AUTH =================
@app.route("/auth", methods=["GET", "POST"])
def auth():

    if request.method == "POST":

        name = request.form["name"]
        password = request.form["password"]
        role = request.form["role"]

        users[name] = {
            "password": password,
            "role": role
        }

        session["user"] = name
        session["role"] = role

        return redirect("/dashboard")

    return STYLE + """
    <div class="container">

        <h2>🧾 Create Account</h2>

        <div class="card">
            <form method="post">

                <input name="name" placeholder="Full Name / Company" required>

                <input name="password" type="password" placeholder="Password" required>

                <select name="role">
                    <option value="admin">👑 Admin</option>
                    <option value="employer">🏢 Employer</option>
                    <option value="employee">👷 Employee</option>
                </select>

                <button>Create Account</button>
            </form>
        </div>

    </div>
    """

# ================= DASHBOARD ROUTER =================
@app.route("/dashboard")
def dashboard():

    role = session.get("role")

    if role == "admin":
        return admin_dashboard()

    if role == "employer":
        return employer_dashboard()

    if role == "employee":
        return employee_dashboard()

    return redirect("/auth")

# ================= ADMIN DASHBOARD =================
def admin_dashboard():
    return STYLE + """
    <div class="nav">
        <h3>Admin Panel</h3>
        <span class="badge">ADMIN</span>
    </div>

    <div class="container">

        <div class="card">
            <h2>👑 System Overview</h2>
            <button>View Users</button>
            <button>Revenue Reports</button>
            <button>Fraud Monitoring</button>
        </div>

    </div>
    """

# ================= EMPLOYER DASHBOARD =================
def employer_dashboard():
    return STYLE + """
    <div class="nav">
        <h3>Employer Dashboard</h3>
        <span class="badge">EMPLOYER</span>
    </div>

    <div class="container">

        <div class="card">
            <h2>🏢 Payroll System</h2>

            <input placeholder="Employee Name">
            <input placeholder="Amount">

            <button>Send Salary (M-Pesa)</button>
        </div>

        <div class="card">
            <h2>💸 Payments</h2>

            <input placeholder="Phone 2547XXXXXX">
            <input placeholder="Amount">

            <button>Send STK Push</button>
        </div>

    </div>
    """

# ================= EMPLOYEE DASHBOARD =================
def employee_dashboard():
    return STYLE + """
    <div class="nav">
        <h3>Employee Dashboard</h3>
        <span class="badge">EMPLOYEE</span>
    </div>

    <div class="container">

        <div class="card">
            <h2>💰 Wallet</h2>
            <h1>KES 0.00</h1>
        </div>

        <div class="card">
            <h2>📲 Withdraw</h2>

            <input placeholder="M-Pesa Number">
            <input placeholder="Amount">

            <button>Withdraw Funds</button>
        </div>

    </div>
    """

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
