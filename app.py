from flask import Flask, request, redirect, session, render_template, url_for, jsonify
import sqlite3, os, bcrypt

# Initialize Flask
app = Flask(__name__)
app.secret_key = "UTE_SECRET_KEY_2026"
DB = "ute.db"

# YOUR INTASEND PUBLIC KEY
INTASEND_PUBLIC_KEY = "ISPubKey_test_5311493a-867d-4ee0-9985-e97bd72f6f71"

def get_db():
    conn = sqlite3.connect(DB, timeout=10)
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
        except: return "Error: Username/Email/Phone already exists."
        finally: conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    conn = get_db()
    res = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()
    balance = res[0] if res else 0
    
    # Get jobs based on role
    if session.get("role") == "employer":
        jobs = conn.execute("SELECT * FROM jobs WHERE employer=?", (session["user"],)).fetchall()
    else:
        jobs = conn.execute("SELECT * FROM jobs WHERE status='open'").fetchall()
        
    conn.close()
    return render_template("dashboard.html", 
                           user=session["user"], 
                           balance=balance, 
                           role=session.get("role"), 
                           jobs=jobs, 
                           is_key=INTASEND_PUBLIC_KEY)

@app.route("/payment_success", methods=["POST"])
def payment_success():
    if "user" not in session: return jsonify({"status": "unauthorized"}), 401
    data = request.json
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
