from flask import Flask, request, redirect, session, render_template, url_for, jsonify
import sqlite3, os, bcrypt

app = Flask(__name__)
app.secret_key = "UTE_SECRET_KEY_2026"

# WE CHANGE THE NAME TO FORCE A NEW DATABASE
DB = "ute_v2.db"

# YOUR PUBLIC KEY
INTASEND_PUBLIC_KEY = "ISPubKey_test_5311493a-867d-4ee0-9985-e97bd72f6f71"

def init_db():
    """This function runs every time the app starts to ensure tables exist."""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # Create Users
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, email TEXT UNIQUE, phone TEXT UNIQUE,
        national_id TEXT UNIQUE, password TEXT, role TEXT, 
        location TEXT, bio_or_company TEXT
    )""")
    # Create Jobs
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, employer TEXT, 
        title TEXT, description TEXT, salary REAL, status TEXT DEFAULT 'open'
    )""")
    # Create Wallet
    c.execute("""CREATE TABLE IF NOT EXISTS wallet (
        username TEXT UNIQUE, balance REAL DEFAULT 0
    )""")
    conn.commit()
    conn.close()
    print("Database Initialized Successfully.")

# ACTIVATE THE DATABASE IMMEDIATELY
init_db()

def get_db():
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        password = d.get("password").encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        conn = get_db()
        try:
            # 1. Insert User
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, bio_or_company) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (d.get("username"), d.get("email"), d.get("phone"), d.get("national_id"), hashed, d.get("role"), d.get("location"), d.get("bio_or_company")))
            
            # 2. Create their Wallet
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (d.get("username"),))
            
            conn.commit()
            session.update({
                "user": d.get("username"), 
                "role": d.get("role"), 
                "phone": d.get("phone"), 
                "email": d.get("email")
            })
            return redirect(url_for("dashboard"))
        except Exception as e:
            return f"Auth Error: {e}. Try a different username/email."
        finally:
            conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth"))
    
    conn = get_db()
    # Get Balance
    res = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()
    balance = res[0] if res else 0
    
    # Get Jobs (Show all for now to keep it simple)
    jobs = conn.execute("SELECT * FROM jobs").fetchall()
    conn.close()
    
    return render_template("dashboard.html", 
                           user=session["user"], 
                           balance=balance, 
                           role=session.get("role"), 
                           jobs=jobs, 
                           is_key=INTASEND_PUBLIC_KEY)

@app.route("/payment_success", methods=["POST"])
def payment_success():
    if "user" not in session: return jsonify({"status": "error"}), 401
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
