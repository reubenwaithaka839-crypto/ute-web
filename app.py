from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_STABLE_V3")

# This helper function prevents the "Internal Server Error" if the DB is busy
def get_db_connection():
    conn = sqlite3.connect(ute.DB, timeout=10)
    conn.row_factory = sqlite3.Row # This makes data easier to read
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
        hashed = bcrypt.hashpw(d.get("password").encode('utf-8'), bcrypt.gensalt())
        conn = get_db_connection()
        try:
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, bio_or_company) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (d.get("username"), d.get("email"), d.get("phone"), d.get("national_id"), hashed, d.get("role"), d.get("location"), d.get("bio_or_company")))
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (d.get("username"),))
            conn.commit()
            session.update({"user": d.get("username"), "role": d.get("role"), "phone": d.get("phone"), "email": d.get("email")})
            return redirect(url_for("dashboard"))
        except Exception as e:
            return f"Auth Error: {e}"
        finally:
            conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    conn = get_db_connection()
    try:
        # Get Balance
        res = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()
        balance = res['balance'] if res else 0
        
        if session["role"] == "employer":
            my_jobs = conn.execute("SELECT * FROM jobs WHERE employer=?", (session["user"],)).fetchall()
            talents = conn.execute("SELECT username, bio_or_company, location FROM users WHERE role='employee'").fetchall()
            return render_template("dashboard.html", user=session["user"], balance=balance, role="employer", my_jobs=my_jobs, talents=talents)
        else:
            available_jobs = conn.execute("SELECT * FROM jobs WHERE status='open'").fetchall()
            return render_template("dashboard.html", user=session["user"], balance=balance, role="employee", jobs=available_jobs)
    except Exception as e:
        return f"Dashboard Error: {e}"
    finally:
        conn.close()

@app.route("/post_job", methods=["POST"])
def post_job():
    if session.get("role") != "employer": return redirect(url_for("dashboard"))
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO jobs (employer, title, description, salary) VALUES (?, ?, ?, ?)",
                     (session["user"], request.form.get("title"), request.form.get("description"), request.form.get("salary")))
        conn.commit()
    except Exception as e:
        return f"Post Job Error: {e}"
    finally:
        conn.close()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
