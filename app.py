from flask import Flask, request, redirect, session, render_template, url_for
import sqlite3, ute, mpesa, os, bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "UTE_FINTECH_2026_SECURE")

# --- DATABASE INITIALIZATION (Runs every time Render starts the app) ---
def start_db():
    try:
        ute.init_db()
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Database Init Error: {e}")

start_db()
# -----------------------------------------------------------------------

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        # Extract data from the form
        un = request.form.get("username")
        em = request.form.get("email")
        ph = request.form.get("phone")
        ni = request.form.get("national_id")
        pw = request.form.get("password")
        ro = request.form.get("role")
        lo = request.form.get("location", "Nairobi")
        sk = request.form.get("skills", "General")

        if not all([un, em, ph, ni, pw]):
            return "Registration Error: Please fill in all required fields (Username, Email, Phone, National ID, Password)."

        hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt())
        
        conn = sqlite3.connect(ute.DB)
        try:
            # Save User
            conn.execute("""INSERT INTO users (username, email, phone, national_id, password, role, location, skills) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                         (un, em, ph, ni, hashed, ro, lo, sk))
            
            # Create Wallet
            conn.execute("INSERT OR IGNORE INTO wallet (username, balance) VALUES (?, 0)", (un,))
            conn.commit()
            
            # Set Session
            session.update({"user": un, "role": ro, "phone": ph, "email": em})
            return redirect(url_for("dashboard"))

        except sqlite3.IntegrityError:
            return "Registration Error: A user with this Email, Phone, or National ID already exists."
        except Exception as e:
            return f"System Error: {e}"
        finally:
            conn.close()
            
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth"))
    
    conn = sqlite3.connect(ute.DB)
    try:
        # Get Balance
        balance_row = conn.execute("SELECT balance FROM wallet WHERE username=?", (session["user"],)).fetchone()
        balance = balance_row[0] if balance_row else 0
        
        # Get Talent pool if Employer
        workers = []
        if session.get("role") == "employer":
            workers = conn.execute("SELECT username, location, skills FROM users WHERE role='employee'").fetchall()
        
        return render_template("dashboard.html", user=session["user"], balance=balance, role=session["role"], data=workers)
    except Exception as e:
        return f"Dashboard Error: {e}"
    finally:
        conn.close()

@app.route("/pay/<worker_name>")
def pay(worker_name):
    if "user" not in session or session.get("role") != "employer":
        return redirect(url_for("auth"))
        
    conn = sqlite3.connect(ute.DB)
    try:
        # Check for existing contract
        c = conn.execute("SELECT id, salary, total_months_paid FROM contracts WHERE employee=?", (worker_name,)).fetchone()
        if not c:
            conn.execute("INSERT INTO contracts (employer, employee, salary) VALUES (?, ?, 50000)", (session["user"], worker_name))
            conn.commit()
            c = conn.execute("SELECT id, salary, total_months_paid FROM contracts WHERE employee=?", (worker_name,)).fetchone()
        
        math = ute.get_ute_math(c[1], c[2])
        
        # 1. Trigger M-Pesa STK Push
        mpesa.initiate_stk_push(session.get("phone"), math['total'], session.get("email"), c[0])
        
        # 2. Update DB (Simulating successful payment for test mode)
        mpesa.trigger_settlement(c[0])
        
        return redirect(url_for("dashboard"))
    except Exception as e:
        return f"Payment Error: {e}"
    finally:
        conn.close()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
