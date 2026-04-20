from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3
import ute
import mpesa
import os
import bcrypt

app = Flask(__name__)
# Secure key for Render
app.secret_key = os.environ.get("SECRET_KEY", "UTE_LOCAL_DEV_KEY_2026")

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        un = request.form.get("username")
        pw = request.form.get("password").encode('utf-8')
        role = request.form.get("role")
        
        # Hash password for Million-Dollar Security
        hashed = bcrypt.hashpw(pw, bcrypt.gensalt())
        
        conn = sqlite3.connect(ute.DB)
        try:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                         (un, hashed, role))
            conn.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            session["user"] = un
            session["role"] = role
            return redirect(url_for("dashboard"))
        except:
            return "Registration Error: User might already exist."
        finally:
            conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    
    conn = sqlite3.connect(ute.DB)
    # Get current balance
    balance = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()[0]
    
    # Get talent for employers
    data = []
    if session["role"] == "employer":
        data = conn.execute("SELECT username, location, skills FROM users WHERE role='employee'").fetchall()
    
    conn.close()
    return render_template("dashboard.html", user=session["user"], balance=balance, role=session["role"], data=data)

@app.route("/pay_invoice/<employee>")
def pay_invoice(employee):
    if "user" not in session: return redirect(url_for("auth"))
    
    conn = sqlite3.connect(ute.DB)
    # Auto-create contract if first time
    c_data = conn.execute("SELECT id, salary, total_months_paid FROM contracts WHERE employee=?", (employee,)).fetchone()
    if not c_data:
        conn.execute("INSERT INTO contracts (employer, employee, salary, total_months_paid) VALUES (?, ?, 50000, 0)", 
                     (session["user"], employee))
        conn.commit()
        c_data = conn.execute("SELECT id, salary, total_months_paid FROM contracts WHERE employee=?", (employee,)).fetchone()
    conn.close()

    math = ute.get_ute_math(c_data[1], c_data[2])
    
    # TRIGGER M-PESA
    # Note: Phone must be 254... format. Replace with real phone from DB in production.
    mpesa.initiate_stk_push(phone="254712345678", amount=math['total'], email="test@ute.com", contract_id=c_data[0])
    
    # Update Ledger
    mpesa.trigger_settlement(c_data[0])
    
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    ute.init_db()
    app.run(debug=True)
