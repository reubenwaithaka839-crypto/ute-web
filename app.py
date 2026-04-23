import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', "RW_PRESTIGE_2026")

bcrypt = Bcrypt(app)

# -----------------------
# DATABASE HANDLER
# -----------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(ute.DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db:
        db.close()

# -----------------------
# INIT DB (SAFE FOR RENDER)
# -----------------------
def init_database():
    with app.app_context():
        ute.init_db()

        db = get_db()
        admin = db.execute("SELECT * FROM users WHERE username='admin'").fetchone()
        if not admin:
            db.execute(
                "INSERT INTO users (username, passcode, role) VALUES (?, ?, ?)",
                ("admin", bcrypt.generate_password_hash("admin").decode("utf-8"), "admin")
            )
            db.commit()

# -----------------------
# ROUTES
# -----------------------

@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")

        if not username or not password:
            flash("All fields required", "error")
            return redirect(url_for("register"))

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, passcode, role) VALUES (?, ?, ?)",
                (username, hashed_pw, role)
            )
            db.commit()
            flash("Registration successful", "success")
            return redirect(url_for("login"))
        except:
            flash("Username already exists", "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()

        if user and bcrypt.check_password_hash(user["passcode"], password):
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

        flash("Invalid credentials", "error")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username=?", (session["username"],)
    ).fetchone()

    jobs = db.execute("SELECT * FROM jobs").fetchall()

    return render_template("dashboard.html", user=user, jobs=jobs)


@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if session.get("role") not in ["employer", "admin"]:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        title = request.form.get("title")
        salary = request.form.get("salary")

        db = get_db()
        db.execute(
            "INSERT INTO jobs (title, salary, poster) VALUES (?, ?, ?)",
            (title, salary, session["username"])
        )
        db.commit()

        flash("Job posted successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("post_job.html")


# -----------------------
# APPLY + PAYMENT GATE
# -----------------------
@app.route("/apply/<int:job_id>")
def apply(job_id):
    if "username" not in session:
        return redirect(url_for("login"))

    return render_template("paymentgate.html", job_id=job_id)


@app.route("/verify_payment/<int:job_id>", methods=["POST"])
def verify_payment(job_id):
    ref = request.form.get("ref")

    if not ref:
        flash("Enter M-Pesa reference", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute(
        "INSERT INTO applications (job_id, applicant, status) VALUES (?, ?, ?)",
        (job_id, session["username"], "paid")
    )
    db.commit()

    flash("Application successful!", "success")
    return redirect(url_for("dashboard"))


# -----------------------
# ADMIN PAYOUT ENGINE
# -----------------------
@app.route("/pay_salary", methods=["POST"])
def pay_salary():
    if session.get("role") != "admin":
        return "Unauthorized", 403

    emp_user = request.form.get("emp_username")
    gross = float(request.form.get("amount"))
    is_first = request.form.get("is_first") == "true"

    results = ute.calculate_prestige_split(gross, is_first)

    db = get_db()
    db.execute(
        "UPDATE users SET balance = balance + ? WHERE username=?",
        (results["employee_net"], emp_user)
    )

    db.execute(
        "UPDATE users SET balance = balance + ? WHERE role='admin'",
        (results["treasury_total"],)
    )

    db.commit()

    flash("Salary processed successfully", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# -----------------------
# START APP
# -----------------------
if __name__ == "__main__":
    init_database()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
