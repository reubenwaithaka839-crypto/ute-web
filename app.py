from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3
import ute
from mpesa import stk_push
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ute_secure_key_2026"

DB = "ute.db"
ute.init_db()

@app.route("/")
def index():
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "employee")

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user:
            if check_password_hash(user[2], password):
                session["user"], session["role"] = username, user[3]
                return redirect(url_for("dashboard"))
            return "Invalid Password. <a href='/auth'>Try again</a>"

        hashed_pw = generate_password_hash(password)
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
            c.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (username,))
            conn.commit()
        except sqlite3.IntegrityError:
            return "User exists."
        finally:
            conn.close()

        session["user"], session["role"] = username, role
        return redirect(url_for("dashboard"))
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    balance = ute.get_balance(session["user"])
    return render_template("dashboard.html", user=session["user"], role=session["role"], balance=balance)

@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if session.get("role") != "employer": return "Unauthorized", 403
    if request.method == "POST":
        ute.add_job(session["user"], request.form["title"], request.form["description"], 
                    request.form["requirements"], request.form["location"], request.form["salary"])
        return redirect(url_for("jobs"))
    return render_template("post_job.html")

@app.route("/jobs")
def jobs():
    if "user" not in session: return redirect(url_for("auth"))
    return render_template("jobs.html", jobs=ute.get_jobs(), role=session["role"])

@app.route("/apply/<int:job_id>")
def apply(job_id):
    if session.get("role") != "employee": return "Unauthorized", 403
    ute.apply_job(job_id, session["user"])
    return render_template("apply_success.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
