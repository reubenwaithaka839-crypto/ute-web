from flask import Flask, request, redirect, session, render_template, url_for, jsonify
import sqlite3, ute, os, bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_GLOBAL_v6_FINAL")

# REPLACE THIS WITH YOUR ACTUAL INTASEND PUBLIC KEY
INTASEND_PUBLIC_KEY = "ISPubKey_test_YOUR_KEY_HERE"

def get_db():
    conn = sqlite3.connect(ute.DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return redirect(url_for("dashboard")) if "user" in session else redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        hashed = bcrypt.hashpw(d.get("password").encode('utf-8'), bcrypt.gensalt())
        conn = get_db()
        try:
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, bio_or_company) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (d.get("username"), d.get("email"), d.get("phone"), d.get("national_id"), hashed, d.get("role"), d.get("location"), d.get("bio_or_company")))
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (d.get("username"),))
            conn.commit()
            session.update({"user": d.get("username"), "role": d.get("role"), "phone": d.get("phone"), "email": d.get("email")})
            return redirect(url_for("dashboard"))
        except Exception as e: return f"Auth Error: {e}"
        finally: conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    conn = get_db()
    res = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()
    balance = res[0] if res else 0
    
    if session["role"] == "employer":
        my_jobs = conn.execute("SELECT * FROM jobs WHERE employer=?", (session["user"],)).fetchall()
        return render_template("dashboard.html", user=session["user"], balance=balance, role="employer", my_jobs=my_jobs, is_key=INTASEND_PUBLIC_KEY)
    else:
        jobs = conn.execute("SELECT * FROM jobs WHERE status='open'").fetchall()
        my_contracts = conn.execute("SELECT * FROM contracts WHERE employee=?", (session["user"],)).fetchall()
        return render_template("dashboard.html", user=session["user"], balance=balance, role="employee", jobs=jobs, my_contracts=my_contracts)

@app.route("/payment_success", methods=["POST"])
def payment_success():
    if "user" not in session: return jsonify({"status": "unauthorized"}), 401
    data = request.json
    # results.net_amount from IntaSend is the money that actually reached you
    amount = float(data.get("amount", 0))
    
    conn = get_db()
    conn.execute("UPDATE wallet SET balance = balance + ? WHERE username=?", (amount, session["user"]))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
