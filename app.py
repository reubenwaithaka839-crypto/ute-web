from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import ute
from mpesa import stk_push

app = Flask(__name__)
app.secret_key = "ute_secret"

DB = "ute.db"

ute.init_db()

# ================= AUTH =================
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user:
            session["user"] = username
            session["role"] = user[3]
            return redirect("/dashboard")

        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  (username, password, role))

        c.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (username,))
        conn.commit()
        conn.close()

        session["user"] = username
        session["role"] = role
        return redirect("/dashboard")

    return """
    <h2>UTE LOGIN</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password"><br><br>
        <select name="role">
            <option value="admin">Admin</option>
            <option value="employer">Employer</option>
            <option value="employee">Employee</option>
        </select><br><br>
        <button>Continue</button>
    </form>
    """

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/auth")

    return f"""
    <h1>UTE DASHBOARD</h1>
    <h3>{session['user']} ({session['role']})</h3>

    <a href="/jobs">View Jobs</a><br>
    <a href="/post_job">Post Job</a><br>
    <a href="/deposit">Deposit M-Pesa</a><br>
    <a href="/logout">Logout</a>
    """

# ================= POST JOB =================
@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if session.get("role") not in ["admin", "employer"]:
        return "Access denied"

    if request.method == "POST":
        ute.add_job(
            session["user"],
            request.form["title"],
            request.form["description"],
            request.form["requirements"],
            request.form["location"],
            request.form["salary"]
        )
        return redirect("/jobs")

    return """
    <h2>Post Job</h2>
    <form method="POST">
        <input name="title"><br>
        <textarea name="description"></textarea><br>
        <textarea name="requirements"></textarea><br>
        <input name="location"><br>
        <input name="salary"><br>
        <button>Post</button>
    </form>
    """

# ================= VIEW JOBS =================
@app.route("/jobs")
def jobs():
    jobs = ute.get_jobs()
    html = "<h2>Jobs</h2>"

    for j in jobs:
        html += f"<p><b>{j[2]}</b> - {j[5]} | {j[6]}</p>"

    return html

# ================= MPESA DEPOSIT =================
@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if request.method == "POST":
        phone = request.form["phone"]
        amount = request.form["amount"]

        stk_push(phone, amount, "https://your-app.onrender.com/callback")

        return "STK SENT"

    return """
    <form method="POST">
        <input name="phone"><br>
        <input name="amount"><br>
        <button>Pay</button>
    </form>
    """

# ================= CALLBACK =================
@app.route("/callback", methods=["POST"])
def callback():
    data = request.json

    try:
        result = data["Body"]["stkCallback"]

        if result["ResultCode"] == 0:
            items = result["CallbackMetadata"]["Item"]

            amount = 0
            phone = ""

            for i in items:
                if i["Name"] == "Amount":
                    amount = i["Value"]
                if i["Name"] == "PhoneNumber":
                    phone = i["Value"]

            user = session.get("user")

            ute.update_balance(user, amount)
            ute.add_transaction(phone, user, amount, "MPESA")

    except:
        pass

    return "OK"

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")

if __name__ == "__main__":
    app.run(debug=True)
