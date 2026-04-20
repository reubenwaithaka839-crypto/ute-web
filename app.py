from flask import Flask, request, redirect, session, render_template, url_for, jsonify
import sqlite3
import ute  # Your local UTE.py
from mpesa import stk_push
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
# Best practice: Use an environment variable for the secret key
app.secret_key = os.environ.get("SECRET_KEY", "ute_secure_key_2026") 

DB = "ute.db"
ute.init_db()

# --- AUTH ROUTES ---

@app.route("/")
def index():
    if "user" in session: 
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", "employee")

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()

        if user:
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
            session["user"], session["role"] = username, role
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            return "Username taken. <a href='/auth'>Try another</a>"
        finally:
            conn.close()
            
    return render_template("auth.html")

# --- DASHBOARD & JOBS ---

@app.route("/dashboard")
def dashboard():
    if "user" not in session: 
        return redirect(url_for("auth"))
    balance = ute.get_balance(session["user"])
    return render_template("dashboard.html", user=session["user"], role=session["role"], balance=balance)

@app.route("/post_job", methods=["GET", "POST"])
def post_job():
    if session.get("role") != "employer": 
        return "Unauthorized", 403
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
        return "Unauthorized", 403
    ute.apply_job(job_id, session["user"])
    return render_template("apply_success.html")

# --- PAYMENTS (M-PESA) ---

@app.route("/deposit", methods=["POST"])
def deposit():
    if "user" not in session: 
        return redirect(url_for("auth"))
    
    phone = request.form.get("phone")
    amount = request.form.get("amount")
    
    # Render URL: replace with your actual Render domain
    callback_url = "https://your-app-name.onrender.com/mpesa_callback" 
    
    response = stk_push(phone, amount, callback_url)
    
    if response.get("ResponseCode") == "0":
        return f"<h3>STK Push Sent to {phone}. Please enter your PIN.</h3><a href='/dashboard'>Back to Dashboard</a>"
    else:
        return f"<h3>Error initiating payment.</h3><p>{response.get('CustomerMessage', 'Try again later')}</p><a href='/dashboard'>Back</a>"

@app.route("/mpesa_callback", methods=["POST"])
def mpesa_callback():
    """
    This route is called by Safaricom servers, not the user's browser.
    """
    data = request.get_json()
    result_code = data['Body']['stkCallback']['ResultCode']
    
    if result_code == 0:
        # Payment was successful
        # In a real app, you'd find the user by phone/MerchantRequestID and update balance
        # Example: ute.update_balance_by_callback(data)
        print("Payment Successful") 
        
    return jsonify({"ResultCode": 0, "ResultDesc": "Success"})

# --- SYSTEM ---

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
