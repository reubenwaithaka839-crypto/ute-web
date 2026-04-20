from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_DEV_2026")

@app.route("/")
def index():
    return redirect(url_for("auth")) if "user" not in session else redirect(url_for("dashboard"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        d = request.form
        hashed = bcrypt.hashpw(d.get("password").encode('utf-8'), bcrypt.gensalt())
        
        conn = sqlite3.connect(ute.DB)
        try:
            # Inserting ALL fields from the form
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, skills) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (d.get("username"), d.get("email"), d.get("phone"), d.get("national_id"), hashed, d.get("role"), d.get("location"), d.get("skills")))
            conn.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (d.get("username"),))
            conn.commit()
            
            session.update({"user": d.get("username"), "role": d.get("role"), "phone": d.get("phone"), "email": d.get("email")})
            return redirect(url_for("dashboard"))
        except Exception as e:
            print(f"DATABASE ERROR: {e}")
            return f"Registration Error: {e}"
        finally:
            conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    conn = sqlite3.connect(ute.DB)
    balance = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()[0]
    workers = conn.execute("SELECT username, location, skills FROM users WHERE role='employee'").fetchall() if session["role"] == "employer" else []
    conn.close()
    return render_template("dashboard.html", user=session["user"], balance=balance, role=session["role"], data=workers)

@app.route("/pay/<worker_name>")
def pay(worker_name):
    if "user" not in session: return redirect(url_for("auth"))
    conn = sqlite3.connect(ute.DB)
    # Check for existing contract
    c = conn.execute("SELECT id, salary, total_months_paid FROM contracts WHERE employee=?", (worker_name,)).fetchone()
    if not c:
        conn.execute("INSERT INTO contracts (employer, employee, salary) VALUES (?, ?, 50000)", (session["user"], worker_name))
        conn.commit()
        c = conn.execute("SELECT id, salary, total_months_paid FROM contracts WHERE employee=?", (worker_name,)).fetchone()
    conn.close()
    
    math = ute.get_ute_math(c[1], c[2])
    mpesa.initiate_stk_push(session["phone"], math['total'], session["email"], c[0])
    mpesa.trigger_settlement(c[0])
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    ute.init_db()
    app.run(debug=True)
