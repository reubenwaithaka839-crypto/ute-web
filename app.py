from flask import Flask, request, redirect, session, render_template, url_for, jsonify
import sqlite3
import ute
from mpesa import stk_push
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "ute_secure_key_2026" 

DB = "ute.db"
ute.init_db()

@app.route("/")
def index():
    if "user" in session: return redirect(url_for("dashboard"))
    return redirect(url_for("auth"))

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        username, password, role = request.form["username"], request.form["password"], request.form.get("role", "employee")
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        if user:
            if check_password_hash(user[2], password):
                session["user"], session["role"] = username, user[3]
                return redirect(url_for("dashboard"))
            return "Invalid Password. <a href='/auth'>Try again</a>"
        hashed_pw = generate_password_hash(password)
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
            c.execute("INSERT INTO wallet (username, balance) VALUES (?, 0)", (username,))
            conn.commit()
            session["user"], session["role"] = username, role
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError: return "Username taken."
        finally: conn.close()
    return render_template("auth.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session: return redirect(url_for("auth"))
    balance = ute.get_balance(session["user"])
    return render_template("dashboard.html", user=session["user"], role=session["role"], balance=balance)

@app.route("/deposit", methods=["POST"])
def deposit():
    if "user" not in session: return redirect(url_for("auth"))
    phone, amount = request.form.get("phone"), request.form.get("amount")
    # REPLACE with your actual Render URL
    callback_url = "https://your-app-name.onrender.com/mpesa_callback" 
    stk_push(phone, amount, callback_url)
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth"))

if __name__ == "__main__":
    app.run(debug=True)
