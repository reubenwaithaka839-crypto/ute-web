from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, re, os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "UTE_SUPER_SECURE_2026"

# AI Fraud Check: Password Complexity
def is_secure(pw):
    return re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", pw)

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        if not is_secure(d['password']):
            return "Error: Password must have Upper, Lower, Number, and Special Character (@#$)."
        
        conn = sqlite3.connect(ute.DB)
        try:
            hpw = generate_password_hash(d['password'])
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, skills) 
                            VALUES (?,?,?,?,?,?,?,?)""", (d['username'], d['email'], d['phone'], d['national_id'], hpw, d['role'], d['location'], d['skills']))
            conn.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (d['username'],))
            conn.commit()
            session.update({"user": d['username'], "role": d['role'], "nid": d['national_id']})
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            return "Error: ID, Email, or Phone already exists in the UTE Ecosystem."
        finally:
            conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    
    conn = sqlite3.connect(ute.DB)
    # Fetch user balance & admin status
    u_data = conn.execute("SELECT balance, is_approved_admin FROM users INNER JOIN wallet ON users.username = wallet.username WHERE users.username=?", (session["user"],)).fetchone()
    conn.close()
    
    return render_template("dashboard.html", user=session["user"], role=session["role"], nid=session["nid"], balance=u_data[0], is_admin=u_data[1])

if __name__ == "__main__":
    ute.init_db()
    app.run(debug=True)
