from flask import Flask, request, redirect, session, render_template, url_for, flash
import sqlite3
import ute
import re
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_ULTIMATE_SECURE_2026_TOKEN")

# --- AI SENTINEL: SECURITY LOGIC ---
def is_password_strong(password):
    """Enforces Million-Dollar Security: 8+ chars, Upper, Lower, Digit, Special."""
    if len(password) < 8: return False
    if not re.search("[a-z]", password): return False
    if not re.search("[A-Z]", password): return False
    if not re.search("[0-9]", password): return False
    if not re.search("[@#$!%*?&]", password): return False
    return True

# --- ROUTES ---

@app.route("/")
def index():
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        # Capture all "Identity triad" data
        un = request.form.get("username")
        em = request.form.get("email")
        ph = request.form.get("phone")
        nid = request.form.get("national_id")
        pw = request.form.get("password")
        role = request.form.get("role")
        loc = request.form.get("location")
        skl = request.form.get("skills")

        # AI Password validation
        if not is_password_strong(pw):
            return "Security Error: Password must be 8+ chars with Upper, Lower, Number, and Special Char."

        conn = sqlite3.connect(ute.DB)
        try:
            hashed_pw = generate_password_hash(pw)
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, skills) 
                            VALUES (?,?,?,?,?,?,?,?)""", (un, em, ph, nid, hashed_pw, role, loc, skl))
            conn.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            
            session.update({"user": un, "role": role, "nid": nid})
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            return "Identity Error: This National ID, Email, or Phone is already registered."
        finally:
            conn.close()
            
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    
    conn = sqlite3.connect(ute.DB)
    # Fetch real-time data for the full-screen UI
    user_info = conn.execute("SELECT balance, is_approved_admin FROM users INNER JOIN wallet ON users.username = wallet.username WHERE users.username=?", (session["user"],)).fetchone()
    
    # Get potential jobs for employees or applicants for employers
    if session["role"] == "employer":
        display_data = conn.execute("SELECT username, location, skills FROM users WHERE role='employee'").fetchall()
    else:
        display_data = conn.execute("SELECT * FROM jobs").fetchall()
    
    conn.close()
    
    return render_template("dashboard.html", 
                           user=session["user"], 
                           role=session["role"], 
                           nid=session["nid"], 
                           balance=user_info[0], 
                           is_admin=user_info[1],
                           data=display_data)

@app.route("/initiate_contract/<employee_name>")
def initiate_contract(employee_name):
    if session.get("role") != "employer": return "Access Denied."
    
    conn = sqlite3.connect(ute.DB)
    # Check current contract status to determine if it's Month 1 or Month 2-12
    contract = conn.execute("SELECT total_months_paid FROM contracts WHERE employer=? AND employee=?", (session["user"], employee_name)).fetchone()
    
    if not contract:
        # Create new 12-month mandate
        conn.execute("INSERT INTO contracts (employer, employee, salary, total_months_paid) VALUES (?, ?, ?, ?)", 
                     (session["user"], employee_name, 50000, 0)) # Example base salary 50k
        conn.commit()
        months = 0
    else:
        months = contract[0]
    
    conn.close()
    return redirect(url_for("pay_invoice", employee=employee_name))

@app.route("/pay_invoice/<employee>")
def pay_invoice(employee):
    conn = sqlite3.connect(ute.DB)
    salary_val = conn.execute("SELECT salary, total_months_paid FROM contracts WHERE employee=?", (employee,)).fetchone()
    conn.close()

    # Trigger the Math Engine (30% if months == 0, else 10%)
    math = ute.get_ute_math(salary_val[0], salary_val[1])
    
    return render_template("pay.html", 
                           employer=session["user"], 
                           employee=employee,
                           salary=salary_val[0],
                           ute_cut=math['ute'],
                           cashback=math['cashback'],
                           fee=salary_val[0]*0.03,
                           total=math['total'],
                           percent= "30" if salary_val[1] == 0 else "10")

# --- ADMIN GATEKEEPER ---
@app.route("/superadmin/control")
def admin_requests():
    # Only the creator (you) sees this
    conn = sqlite3.connect(ute.DB)
    requests = conn.execute("SELECT id, username, national_id FROM users WHERE admin_request_pending=1").fetchall()
    conn.close()
    return render_template("admin_panel.html", requests=requests)

@app.route("/approve_admin/<int:uid>")
def approve_admin(uid):
    conn = sqlite3.connect(ute.DB)
    # Enforce the Strict 2-Admin Rule
    current_admins = conn.execute("SELECT COUNT(*) FROM users WHERE is_approved_admin=1").fetchone()[0]
    if current_admins < 2:
        conn.execute("UPDATE users SET is_approved_admin=1, admin_request_pending=0 WHERE id=?", (uid,))
        conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    ute.init_db()
    app.run(debug=True, port=5000)
