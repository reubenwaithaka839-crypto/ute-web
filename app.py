from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, bcrypt

app = Flask(__name__)
# Secure session management
app.secret_key = os.environ.get("SECRET_KEY", "UTE_MARKETPLACE_2026")

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        un, em, ph, ni, pw, ro = d.get("username"), d.get("email"), d.get("phone"), d.get("national_id"), d.get("password"), d.get("role")
        
        if not all([un, em, ph, ni, pw]):
            return "Error: All registration fields are required."

        hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        conn = sqlite3.connect(ute.DB)
        try:
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, skills) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (un, em, ph, ni, hashed, ro, d.get("location", "Nairobi"), d.get("skills", "General")))
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            session.update({"user": un, "role": ro, "phone": ph, "email": em})
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            return "Error: Identity already registered (Check Email, Phone, or ID)."
        finally:
            conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    
    conn = sqlite3.connect(ute.DB)
    # Get user's current wallet balance
    bal_row = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()
    balance = bal_row[0] if bal_row else 0
    
    if session["role"] == "employer":
        # Employers see jobs they posted and available workers
        my_jobs = conn.execute("SELECT * FROM jobs WHERE employer=?", (session["user"],)).fetchall()
        talents = conn.execute("SELECT username, skills, location FROM users WHERE role='employee'").fetchall()
        conn.close()
        return render_template("dashboard.html", user=session["user"], balance=balance, role=session["role"], my_jobs=my_jobs, talents=talents)
    else:
        # Employees see all available open jobs
        jobs = conn.execute("SELECT * FROM jobs WHERE status='open'").fetchall()
        conn.close()
        return render_template("dashboard.html", user=session["user"], balance=balance, role=session["role"], jobs=jobs)

@app.route("/post_job", methods=["POST"])
def post_job():
    if session.get("role") != "employer": return redirect(url_for("dashboard"))
    
    title = request.form.get("title")
    desc = request.form.get("description")
    sal = request.form.get("salary")
    
    conn = sqlite3.connect(ute.DB)
    conn.execute("INSERT INTO jobs (employer, title, description, salary) VALUES (?, ?, ?, ?)",
                 (session["user"], title, desc, sal))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/hire/<int:job_id>/<worker_name>")
def hire(job_id, worker_name):
    if session.get("role") != "employer": return redirect(url_for("dashboard"))
    
    conn = sqlite3.connect(ute.DB)
    # 1. Get job details
    job = conn.execute("SELECT salary FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job: return "Job not found."
    
    # 2. Create the contract
    conn.execute("INSERT INTO contracts (employer, employee, salary) VALUES (?, ?, ?)", 
                 (session["user"], worker_name, job[0]))
    # 3. Mark job as closed
    conn.execute("UPDATE jobs SET status='closed' WHERE id=?", (job_id,))
    conn.commit()
    
    # 4. Trigger M-Pesa (Using Month 0 math for 30% fee)
    math = ute.get_ute_math(job[0], 0)
    mpesa.initiate_stk_push(session["
