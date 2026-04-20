from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, re
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = "UTE_MILLION_DOLLAR_SECRET_2026"

# --- CORE ROUTES ---

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        # Strong Password AI Check
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", d['password']):
            return "Security Alert: Password too weak. Use A-Z, a-z, 0-9 and Symbols."
        
        conn = sqlite3.connect(ute.DB)
        try:
            hpw = generate_password_hash(d['password'])
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, skills) 
                            VALUES (?,?,?,?,?,?,?,?)""", (d['username'], d['email'], d['phone'], d['national_id'], hpw, d['role'], d['location'], d['skills']))
            conn.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (d['username'],))
            conn.commit()
            session.update({"user": d['username'], "role": d['role'], "nid": d['national_id']})
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError: return "Identity Error: ID or Phone already exists."
        finally: conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    conn = sqlite3.connect(ute.DB)
    # Alignment Logic: Show employees to employers based on location
    u_info = conn.execute("SELECT balance, is_approved_admin FROM users INNER JOIN wallet ON users.username = wallet.username WHERE users.username=?", (session["user"],)).fetchone()
    
    data = []
    if session["role"] == "employer":
        # MILLION DOLLAR ALIGNMENT: Show skills and location matches
        data = conn.execute("SELECT username, location, skills, id FROM users WHERE role='employee'").fetchall()
    
    conn.close()
    return render_template("dashboard.html", user=session["user"], role=session["role"], nid=session["nid"], balance=u_info[0], is_admin=u_info[1], data=data)

# --- ADMIN ROUTES (The Gatekeeper) ---

@app.route("/superadmin/ute")
def superadmin():
    # Only you access this
    conn = sqlite3.connect(ute.DB)
    requests = conn.execute("SELECT id, username, national_id FROM users WHERE admin_request_pending=1").fetchall()
    admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE is_approved_admin=1").fetchone()[0]
    org_count = conn.execute("SELECT COUNT(*) FROM users WHERE role='employer'").fetchone()[0]
    total_rev = conn.execute("SELECT SUM(ute_share) FROM ledger").fetchone()[0] or 0
    conn.close()
    return render_template("admin_panel.html", requests=requests, admin_count=admin_count, org_count=org_count, total_ute_revenue=total_rev)

@app.route("/approve_admin/<int:uid>")
def approve_admin(uid):
    conn = sqlite3.connect(ute.DB)
    count = conn.execute("SELECT COUNT(*) FROM users WHERE is_approved_admin=1").fetchone()[0]
    if count < 2:
        conn.execute("UPDATE users SET is_approved_admin=1, admin_request_pending=0 WHERE id=?", (uid,))
        conn.commit()
    conn.close()
    return redirect(url_for("superadmin"))

if __name__ == "__main__":
    ute.init_db()
    app.run(debug=True)
