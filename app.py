from flask import Flask, request, redirect, session, render_template_string
from ute import UTE
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ute-secret-key")

ute = UTE()

# ================= UI STYLE =================
STYLE = """
<style>
body {
    margin: 0;
    font-family: Arial;
    background: #0f172a;
    color: white;
}
.center {
    text-align: center;
    margin-top: 120px;
}
.card {
    background: rgba(255,255,255,0.08);
    padding: 20px;
    margin: 10px;
    border-radius: 12px;
}
button {
    padding: 10px 20px;
    border: none;
    background: #38bdf8;
    color: black;
    border-radius: 8px;
}
input {
    padding: 10px;
    width: 80%;
    margin: 5px;
}
</style>
"""

# ================= HOME =================
@app.route("/")
def home():
    return STYLE + """
    <div class="center">
        <h1>🌍 UTE PLATFORM</h1>
        <a href="/auth?role=company"><button>Company</button></a>
        <a href="/auth?role=worker"><button>Worker</button></a>
        <a href="/auth?role=admin"><button>Admin</button></a>
    </div>
    """

# ================= AUTH =================
@app.route("/auth", methods=["GET", "POST"])
def auth():
    role = request.args.get("role")

    if request.method == "POST":
        name = request.form["name"]
        password = request.form["password"]

        ute.register_company(name, password)
        user = ute.login_company(name, password)

        if user:
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
            <input name="name" placeholder="Name" required><br>
            <input name="password" type="password" placeholder="Password" required><br>
            <button>Login</button>
        </form>
    </div>
    """

# ================= COMPANY =================
@app.route("/company")
def company():
    if session.get("role") != "company":
        return redirect("/")

    employees = ute.get_company_employees(session["user"])

    html = "".join([f"<div class='card'>{e[0]} - {e[1]} months</div>" for e in employees])

    return STYLE + f"""
    <h2>Company Dashboard</h2>

    <div class="card">
        <form method="post" action="/process">
            <input name="employee" placeholder="Employee"><br>
            <input name="salary" placeholder="Salary"><br>
            <button>Process Salary</button>
        </form>
    </div>

    {html}
    """

@app.route("/process", methods=["POST"])
def process():
    ute.process_salary(
        session["user"],
        request.form["employee"],
        request.form["salary"],
        False
    )
    return redirect("/company")

# ================= WORKER =================
@app.route("/worker")
def worker():
    jobs = ute.get_jobs()

    html = "".join([
        f"<div class='card'><h3>{j['title']}</h3><p>{j['location']}</p><p>KES {j['salary']}</p></div>"
        for j in jobs
    ])

    return STYLE + f"""
    <h2>Jobs</h2>
    {html}
    """

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/")

    tx = ute.get_transactions()

    tx_html = "".join([
        f"<div class='card'>{t[0]} → {t[1]} | +{t[2]}</div>"
        for t in tx
    ])

    return STYLE + f"""
    <h2>Admin Dashboard</h2>

    <div class="card">
        Revenue: KES {ute.get_revenue()}
    </div>

    {tx_html}
    """

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
