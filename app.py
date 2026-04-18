from flask import Flask, request, redirect, session, render_template, url_for, jsonify
import sqlite3
import ute
from mpesa import stk_push
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ute_secure_key_2026" # Keep this secret

DB = "ute.db"
ute.init_db()

# ================= HOME REDIRECT =================
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth"))

# ================= AUTHENTICATION =================
@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form.get("role", "employee")

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user:
            # Login existing user
            if check_password_hash(user[2], password):
                session["user"], session["role"] = username, user[3]
                return redirect(url_for("dashboard"))
            return "Invalid Password. <a href='/auth'>Try again</a>"

        # Register new user
        hashed_pw = generate_password_hash(password)
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
            c.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (username,))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username taken."
        finally:
            conn.close()

        session["user"], session["role"] = username, role
        return redirect(url_for("dashboard"))
    return render_template("auth.html")

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth"))
    
    balance = ute.get_balance(session["user"])
    return render_template("dashboard.html", 
                           user=session["user"], 
                           role=session["role"], 
                           balance=balance)

# ================= JOB MANAGEMENT =================
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
    return render_template("jobs.html", jobs=ute.get_jobs(), role=session["role"])

@app.route("/apply/<int:job_id>")
def apply(job_id):
    if session.get("role") != "employee":
        return "Only employees can apply", 403
    ute.apply_job(job_id, session["user"])
    return render_template("apply_success.html")

# ================= M-PESA PAYMENTS =================
@app.route("/deposit", methods=["POST"])
def deposit():
    if "user" not in session:
        return redirect(url_for("auth"))
    
    phone = request.form.get("phone")
    amount = request.form.get("amount")
    
    # Replace 'your-app-name' with your actual Render URL
    callback_url = "https://your-app-name.onrender.com/mpesa_callback"
    
    # Trigger the phone popup
    stk_push(phone, amount, callback_url)
    
    return f"""
    <div style="text-align:center; margin-top:50px; font-family:sans-serif;">
        <h2>STK Push Sent!</h2>
        <p>Check your phone and enter your M-Pesa PIN for Ksh {amount}.</p>
        <a href="/dashboard" style="text-decoration:none; color:blue;">Return to Dashboard</a>
    </div>
    """

@app.route("/mpesa_callback", methods=["POST"])
def mpesa_callback():
    data = request.get_json()
    result_code = data['Body']['stkCallback']['ResultCode']
    
    if result_code == 0:
        # Payment was successful
        items = data['Body']['stkCallback']['CallbackMetadata']['Item']
        amount = next(i['Value'] for i in items if i['Name'] == 'Amount')
        phone = next(i['Value'] for i in items if i['Name'] == 'PhoneNumber')
        
        # Note: In production, you'd match the phone number to a user 
        # For now, we print to logs to verify it works
        print(f"SUCCESS: Received Ksh {amount} from {phone}")
        
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
