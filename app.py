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
        <input name="username"><br><br>
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

    user = session["user"]
    role = session["role"]

    html = f"""
    <h1>UTE DASHBOARD</h1>
    <h3>{user} ({role})</h3>

    <a href="/jobs">View Jobs</a><br>
    """

    if role == "employer":
        html += "<a href='/post_job'>Post Job</a><br>"

    if role == "employee":
        html += "<a href='/jobs'>Apply for Jobs</a><br>"

    html += "<a href='/logout'>Logout</a>"

    return html

# ================= POST JOB (ONLY EMPLOYER) =================
@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if session.get("role") != "employer":
        return "Only employers can post jobs"

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

# ================= VIEW JOBS (ALL USERS) =================
@app.route("/jobs")
def jobs():
    jobs = ute.get_jobs()

    html = "<h2>Available Jobs</h2>"

    for j in jobs:
        html += f"""
        <div style="border:1px solid #ccc;padding:10px;margin:10px;">
            <h3>{j[2]}</h3>
            <p>{j[3]}</p>
            <p><b>Requirements:</b> {j[4]}</p>
            <p><b>Location:</b> {j[5]}</p>
            <p><b>Salary:</b> {j[6]}</p>
        """

        if session.get("role") == "employee":
            html += f"<a href='/apply/{j[0]}'>Apply</a>"

        html += "</div>"

    return html

# ================= APPLY JOB =================
@app.route("/apply/<int:job_id>")
def apply(job_id):
    if session.get("role") != "employee":
        return "Only employees can apply"

    ute.apply_job(job_id, session["user"])
    return "Applied successfully"

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")

if __name__ == "__main__":
    app.run(debug=True)
