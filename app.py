from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "UTE_SECRET_MILLION_2026"

# AI Security Check
def is_secure(pw):
    return re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", pw)

@app.route("/")
def index():
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        if not is_secure(d['password']): return "Security Alert: Password too weak."
        conn = sqlite3.connect(ute.DB)
        try:
            hpw = generate_password_hash(d['password'])
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, skills) 
                            VALUES (?,?,?,?,?,?,?,?)""", (d['username'], d['email'], d['phone'], d['national_id'], hpw, d['role'], d['location'], d['skills']))
            conn.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (d['username'],))
            conn.commit()
            session.update({"user": d['username'], "role": d['role'], "nid": d['national_id']})
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError: return "Identity Alert: ID/Phone already exists."
        finally: conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    conn = sqlite3.connect(ute.DB)
    u_info = conn.execute("SELECT balance, is_approved_admin FROM users INNER JOIN wallet ON users.username = wallet.username WHERE users.username=?", (session["user"],)).fetchone()
    data = []
    if session["role"] == "employer":
        data = conn.execute("SELECT username, location, skills FROM users WHERE role='employee'").fetchall()
    conn.close()
    return render_template("dashboard.html", user=session["user"], role=session["role"], nid=session["nid"], balance=u_info[0], is_admin=u_info[1], data=data)

@app.route("/pay_invoice/<employee>")
def pay_invoice(employee):
    if "user" not in session: return redirect(url_for("auth"))
    conn = sqlite3.connect(ute.DB)
    # Get or create 12-month mandate
    c_data = conn.execute("SELECT id, salary, total_months_paid FROM contracts WHERE employee=?", (employee,)).fetchone()
    if not c_data:
        conn.execute("INSERT INTO contracts (employer, employee, salary, total_months_paid) VALUES (?, ?, ?, ?)", (session["user"], employee, 50000, 0))
        conn.commit()
        c_data = conn.execute("SELECT id, salary, total_months_paid FROM contracts WHERE employee=?", (employee,)).fetchone()
    conn.close()
    
    math = ute.get_ute_math(c_data[1], c_data[2])
    return render_template("pay.html", m=math, emp=employee, cid=c_data[0])

@app.route("/execute_payment/<int:cid>")
def execute_payment(cid):
    if mpesa.trigger_settlement(cid):
        return redirect(url_for("dashboard"))
    return "Payment Failed."

if __name__ == "__main__":
    ute.init_db()
    app.run(debug=True)
