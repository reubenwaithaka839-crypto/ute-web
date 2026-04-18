from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3
import ute
from mpesa import stk_push
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ute_secret_key_change_this_later"

DB = "ute.db"

# Initialize the database on startup
ute.init_db()

# ================= AUTHENTICATION =================
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user:
            # Check if password matches the hash
            if check_password_hash(user[2], password):
                session["user"] = username
                session["role"] = user[3]
                return redirect(url_for("dashboard"))
            else:
                return "Invalid Password. <a href='/auth'>Try again</a>"

        # Register New User with Hashed Password
        hashed_pw = generate_password_hash(password)
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, hashed_pw, role))
            c.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (username,))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists."
        finally:
            conn.close()

        session["user"] = username
        session["role"] = role
        return redirect(url_for("dashboard"))

    return render_template("auth.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth"))

    user = session["user"]
    role = session["role"]
    balance = ute.get_balance(user)

    return render_template("dashboard.html", user=user, role=role, balance=balance)

# ================= JOBS LOGIC =================
@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if session.get("role") != "employer":
        return "Unauthorized Access", 403

    if request.method == "POST":
        ute.add_job(
            session["user"],
            request.form["title"],
            request.form["description"],
            request.form["requirements"],
            request.form["location"],
            request.form["salary"]
        )
        return redirect(url_for("jobs"))

    return render_template("post_job.html")

@app.route("/jobs")
def jobs():
    if "user" not in session:
        return redirect(url_for("auth"))
    
    all_jobs = ute.get_jobs()
    return render_template("jobs.html", jobs=all_jobs, role=session.get("role"))

@app.route("/apply/<int:job_id>")
def apply(job_id):
    if session.get("role") != "employee":
        return "Only employees can apply", 403

    ute.apply_job(job_id, session["user"])
    return redirect(url_for("jobs"))

# ================= PAYMENTS =================
@app.route("/deposit", methods=["POST"])
def deposit():
    if "user" not in session:
        return redirect(url_for("auth"))
    
    phone = request.form["phone"]
    amount = request.form["amount"]
    
    # Render URL for callback (ensure this is your public Render URL)
    callback_url = "https://your-app-name.onrender.com/mpesa_callback"
    
    response = stk_push(phone, amount, callback_url)
    return f"STK Push Sent: {response.get('CustomerMessage', 'Check your phone')}"

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
