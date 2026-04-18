from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = "ute-secret-key"

# ================= SIMPLE STORAGE (TEMP IN MEMORY) =================
users = {}

# ================= HOME =================
@app.route("/")
def home():
    return """
    <h1>UTE SYSTEM</h1>
    <a href="/auth">Register / Login</a>
    """

# ================= REGISTRATION =================
@app.route("/auth", methods=["GET", "POST"])
def auth():

    if request.method == "POST":

        name = request.form["name"]
        password = request.form["password"]
        role = request.form["role"]

        # store user
        users[name] = {
            "password": password,
            "role": role
        }

        session["user"] = name
        session["role"] = role

        return redirect("/dashboard")

    return """
    <h2>Create Account</h2>

    <form method="post">
        <input name="name" placeholder="Full Name / Company"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>

        <select name="role">
            <option value="admin">Admin</option>
            <option value="employer">Employer</option>
            <option value="employee">Employee</option>
        </select><br><br>

        <button>Create Account</button>
    </form>
    """

# ================= DASHBOARD ROUTING =================
@app.route("/dashboard")
def dashboard():

    role = session.get("role")

    if role == "admin":
        return admin_dashboard()

    elif role == "employer":
        return employer_dashboard()

    elif role == "employee":
        return employee_dashboard()

    return redirect("/auth")

# ================= ADMIN DASHBOARD =================
def admin_dashboard():
    return """
    <h2>👑 Admin Dashboard</h2>

    <button>View Users</button><br><br>
    <button>System Reports</button><br><br>
    <button>Revenue Overview</button>
    """

# ================= EMPLOYER DASHBOARD =================
def employer_dashboard():
    return """
    <h2>🏢 Employer Dashboard</h2>

    <button>Pay Employees</button><br><br>
    <button>Manage Payroll</button><br><br>
    <button>M-Pesa Payments</button>
    """

# ================= EMPLOYEE DASHBOARD =================
def employee_dashboard():
    return """
    <h2>👷 Employee Dashboard</h2>

    <button>View Salary</button><br><br>
    <button>Withdraw</button><br><br>
    <button>Transactions</button>
    """

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
