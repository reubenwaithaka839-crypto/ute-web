from flask import Flask, request, redirect, session, render_template, url_for, jsonify
import sqlite3, ute, re, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_SUPREME_SECURE_2026")

# --- AI SECURITY UTILS ---
def password_check(pw):
    # Enforces: 8+ chars, Upper, Lower, Number, Special Char
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"
    return re.match(pattern, pw)

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        un = request.form['username']
        em = request.form['email']
        ph = request.form['phone']
        nid = request.form['national_id']
        pw = request.form['password']
        role = request.form['role']

        if not password_check(pw):
            return "Error: Password must be strong (A-Z, a-z, 0-9, @#$)."

        conn = sqlite3.connect(ute.DB)
        try:
            hashed = generate_password_hash(pw)
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role) 
                            VALUES (?,?,?,?,?,?)""", (un, em, ph, nid, hashed, role))
            conn.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            session.update({"user": un, "role": role, "nid": nid})
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            return "Error: ID, Phone, or Email already registered."
        finally:
            conn.close()

    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    
    conn = sqlite3.connect(ute.DB)
    # Admin Protection Logic
    is_admin = conn.execute("SELECT is_approved_admin FROM users WHERE username=?", (session["user"],)).fetchone()[0]
    balance = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()[0]
    conn.close()

    return render_template("dashboard.html", 
                           user=session["user"], 
                           role=session["role"], 
                           nid=session["nid"], 
                           balance=balance,
                           is_admin=is_admin)

if __name__ == "__main__":
    ute.init_db()
    app.run(debug=True)
