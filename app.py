from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_MARKET_V4")

def get_db():
    conn = sqlite3.connect(ute.DB, timeout=10)
    return conn

@app.route("/")
def index():
    return redirect(url_for("dashboard")) if "user" in session else redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        un, em, ph, ni, pw, ro = d.get("username"), d.get("email"), d.get("phone"), d.get("national_id"), d.get("password"), d.get("role")
        loc, bio = d.get("location"), d.get("bio_or_company")
        hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        conn = get_db()
        try:
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, bio_or_company) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (un, em, ph, ni, hashed, ro, loc, bio))
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            session.update({"user": un, "role": ro, "phone": ph, "email": em})
            return redirect(url_for("dashboard"))
        except Exception as e: return f"Auth Error: {e}"
        finally: conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    conn = get_db()
    try:
        res = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()
        balance = res[0] if res else 0
        
        if session["role"] == "employer":
            my_jobs = conn.execute("SELECT * FROM jobs WHERE employer=?", (session["user"],)).fetchall()
            talents = conn.execute("SELECT username, bio_or_company, location FROM users WHERE role='employee'").fetchall()
            return render_template("dashboard.html", user=session["user"], balance=balance, role="employer", my_jobs=my_jobs, talents=talents)
        else:
            # Show only OPEN jobs to employees
            jobs = conn.execute("SELECT * FROM jobs WHERE status='open'").fetchall()
            # Show jobs they have ALREADY accepted
            my_contracts = conn.execute("SELECT * FROM contracts WHERE employee=?", (session["user"],)).fetchall()
            return render_template("dashboard.html", user=session["user"], balance=balance, role="employee", jobs=jobs, my_contracts=my_contracts)
    except Exception as e: return f"Dashboard Error: {e}"
    finally: conn.close()

@app.route("/post_job", methods=["POST"])
def post_job():
    if session.get("role") != "employer": return redirect(url_for("dashboard"))
    conn = get_db()
    try:
        conn.execute("INSERT INTO jobs (employer, title, description, salary) VALUES (?, ?, ?, ?)",
                     (session["user"], request.form.get("title"), request.form.get("description"), request.form.get("salary")))
        conn.commit()
    finally: conn.close()
    return redirect(url_for("dashboard"))

@app.route("/apply/<int:job_id>")
def apply(job_id):
    if session.get("role") != "employee": return redirect(url_for("dashboard"))
    conn = get_db()
    try:
        job = conn.execute("SELECT employer, salary FROM jobs WHERE id=?", (job_id,)).fetchone()
        if job:
            # Create the binding contract
            conn.execute("INSERT INTO contracts (employer, employee, salary) VALUES (?, ?, ?)", 
                         (job[0], session["user"], job[1]))
            # Close the job so it's no longer public
            conn.execute("UPDATE jobs SET status='closed' WHERE id=?", (job_id,))
            conn.commit()
    finally: conn.close()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
