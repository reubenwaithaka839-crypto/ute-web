from flask import Flask, request, redirect, session, render_template_string
import sqlite3
import ute

app = Flask(__name__)
app.secret_key = "ute_secret"

DB = "ute.db"

# ---------------- DASHBOARD ----------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/auth")
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/auth")

    user = session["user"]
    role = session["role"]

    return render_template_string(f"""
    <html>
    <body style="font-family:Arial;background:#0f172a;color:white;text-align:center;">

        <h1>UTE DASHBOARD</h1>
        <h3>{user} ({role})</h3>

        <a href="/jobs"><button>📋 View Jobs</button></a><br><br>
        <a href="/post_job"><button>🧑‍💼 Post Job</button></a><br><br>
        <a href="/logout"><button>🚪 Logout</button></a>

    </body>
    </html>
    """)

# ---------------- AUTH ----------------
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

        c.execute("INSERT INTO users VALUES (NULL, ?, ?, ?)", (username, password, role))
        c.execute("INSERT INTO wallet VALUES (NULL, ?, 0)", (username,))
        conn.commit()
        conn.close()

        session["user"] = username
        session["role"] = role
        return redirect("/dashboard")

    return """
    <h2>UTE LOGIN</h2>
    <form method="POST">
        <input name="username" placeholder="Username"><br><br>
        <input name="password" type="password" placeholder="Password"><br><br>

        <select name="role">
            <option value="admin">Admin</option>
            <option value="employer">Employer</option>
            <option value="employee">Employee</option>
        </select><br><br>

        <button>Login / Register</button>
    </form>
    """

# ---------------- POST JOB ----------------
@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if "user" not in session:
        return redirect("/auth")

    if session["role"] not in ["employer", "admin"]:
        return "Access denied"

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        requirements = request.form["requirements"]
        location = request.form["location"]
        salary = request.form["salary"]

        ute.add_job(
            session["user"],
            title,
            description,
            requirements,
            location,
            salary
        )

        return redirect("/jobs")

    return """
    <h2>Post Job</h2>
    <form method="POST">
        <input name="title" placeholder="Job Title"><br><br>
        <textarea name="description" placeholder="Description"></textarea><br><br>
        <textarea name="requirements" placeholder="Requirements"></textarea><br><br>
        <input name="location" placeholder="Location"><br><br>
        <input name="salary" placeholder="Salary"><br><br>
        <button>Post Job</button>
    </form>
    """

# ---------------- VIEW JOBS ----------------
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
            <small>Posted by: {j[1]}</small>
        </div>
        """

    return html

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/auth")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
