from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_MODERN_v2")

@app.route("/")
def index():
    return redirect(url_for("dashboard")) if "user" in session else redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        hashed = bcrypt.hashpw(d.get("password").encode('utf-8'), bcrypt.gensalt())
        conn = sqlite3.connect(ute.DB)
        try:
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, bio_or_company) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (d.get("username"), d.get("email"), d.get("phone"), d.get("national_id"), hashed, d.get("role"), d.get("location"), d.get("bio_or_company")))
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (d.get("username"),))
            conn.commit()
            session.update({"user": d.get("username"), "role": d.get("role"), "phone": d.get("phone"), "email": d.get("email")})
            return redirect(url_for("dashboard"))
        except: return "Registration Error: User or Email already exists."
        finally: conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    conn = sqlite3.connect(ute.DB)
    balance = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()[0]
    
    if session["role"] == "employer":
        my_jobs = conn.execute("SELECT * FROM jobs WHERE employer=?", (session["user"],)).fetchall()
        talents = conn.execute("SELECT username, bio_or_company, location FROM users WHERE role='employee'").fetchall()
        conn.close()
        return render_template("dashboard.html", user=session["user"], balance=balance, role="employer", my_jobs=my_jobs, talents=talents)
    else:
        available_jobs = conn.execute("SELECT * FROM jobs WHERE status='open'").fetchall()
        conn.close()
        return render_template("dashboard.html", user=session["user"], balance=balance, role="employee", jobs=available_jobs)

@app.route("/post_job", methods=["POST"])
def post_job():
    if session.get("role") != "employer": return redirect(url_for("dashboard"))
    conn = sqlite3.connect(ute.DB)
    conn.execute("INSERT INTO jobs (employer, title, description, salary) VALUES (?, ?, ?, ?)",
                 (session["user"], request.form.get("title"), request.form.get("description"), request.form.get("salary")))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
