from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_FINAL_STABLE_2026")

def get_db():
    conn = sqlite3.connect(ute.DB, timeout=10)
    return conn

@app.route("/")
def index():
    return redirect(url_for("dashboard")) if "user" in session else redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        un, em, ph, ni, pw, ro = d.get("username"), d.get("email"), d.get("phone"), d.get("national_id"), d.get("password"), d.get("role")
        loc, bio = d.get("location"), d.get("bio_or_company")

        hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        conn = get_db()
        try:
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, bio_or_company) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (un, em, ph, ni, hashed, ro, loc, bio))
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            session.update({"user": un, "role": ro, "phone": ph, "email": em})
            return redirect(url_for("dashboard"))
        except Exception as e:
            return f"Registration Error: {e}"
        finally:
            conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth"))
    
    conn = get_db()
    try:
        # FIX: Check if wallet exists to prevent 'NoneType' error
        res = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()
        
        if res is None:
            # If wallet is missing (common after a redeploy), create it on the fly
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (session["user"],))
            conn.commit()
            balance = 0.0
        else:
            balance = res[0]
        
        if session["role"] == "employer":
            my_jobs = conn.execute("SELECT * FROM jobs WHERE employer=?", (session["user"],)).fetchall()
            talents = conn.execute("SELECT username, bio_or_company, location FROM users WHERE role='employee'").fetchall()
            return render_template("dashboard.html", user=session["user"], balance=balance, role="employer", my_jobs=my_jobs, talents=talents)
        else:
            jobs = conn.execute("SELECT * FROM jobs WHERE status='open'").fetchall()
            return render_template("dashboard.html", user=session["user"], balance=balance, role="employee", jobs=jobs)
    except Exception as e:
        return f"Dashboard Access Error: {e}"
    finally:
        conn.close()

@app.route("/post_job", methods=["POST"])
def post_job():
    if session.get("role") != "employer":
        return redirect(url_for("dashboard"))
    
    title = request.form.get("title")
    desc = request.form.get("description")
    sal = request.form.get("salary")
    
    conn = get_db()
    try:
        conn.execute("INSERT INTO jobs (employer, title, description, salary) VALUES (?, ?, ?, ?)",
                     (session["user"], title, desc, float(sal) if sal else 0))
        conn.commit()
    except Exception as e:
        return f"Job Posting Error: {e}"
    finally:
        conn.close()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
