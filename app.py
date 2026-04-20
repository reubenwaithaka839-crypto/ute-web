from flask import Flask, request, redirect, session, render_template, url_for, jsonify
import sqlite3, ute, re, os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "MillionDollarSecret2026")

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        un, em, ph, nid, pw, role = request.form['username'], request.form['email'], request.form['phone'], request.form['national_id'], request.form['password'], request.form['role']
        
        # Password AI: Check complexity
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$", pw):
            return "Password too weak. Needs Upper, Lower, Number, and Special Char."

        conn = sqlite3.connect(ute.DB)
        try:
            hashed = generate_password_hash(pw)
            conn.execute("INSERT INTO users (username, email, phone, national_id, password, role) VALUES (?,?,?,?,?,?)", (un, em, ph, nid, hashed, role))
            conn.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            session.update({"user": un, "role": role, "nid": nid})
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError: return "ID, Email or Phone already exists."
        finally: conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    return render_template("dashboard.html", user=session["user"], role=session["role"], nid=session["nid"], balance=ute.get_balance(session["user"]))

@app.route("/admin_approve/<int:uid>")
def admin_approve(uid):
    # Only you (the creator) should access this logic
    conn = sqlite3.connect(ute.DB)
    count = conn.execute("SELECT count(*) FROM users WHERE is_approved_admin=1").fetchone()[0]
    if count < 2:
        conn.execute("UPDATE users SET is_approved_admin=1 WHERE id=?", (uid,))
        conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    ute.init_db()
    app.run(debug=True)
