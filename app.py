import sqlite3, os, uuid, hashlib
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
import ute
from mpesa import payments

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'RW_SUPERMAX_SECURE_2026')
bcrypt = Bcrypt(app)
DB = ute.DB

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # Comprehensive Schema for v4
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT UNIQUE, 
        password TEXT, role TEXT, phone TEXT, bank_name TEXT, acc_number TEXT, 
        referral_code TEXT, referred_by TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, category TEXT, salary REAL, 
        employer TEXT, description TEXT, status TEXT DEFAULT 'live')""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER, applicant TEXT, 
        payment_status TEXT DEFAULT 'unpaid', applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS wallet (
        username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)""")
    conn.commit()
    conn.close()

init_db()

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, e, p = request.form['username'], request.form['email'], generate_password_hash(request.form['password'])
        ref_code = hashlib.md5(u.encode()).hexdigest()[:6].upper()
        query_db("INSERT INTO users (username, email, password, role, referral_code) VALUES (?,?,?,?,?)", 
                 (u, e, p, 'talent', ref_code), commit=True)
        query_db("INSERT INTO wallet (username) VALUES (?)", (u,), commit=True)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = query_db("SELECT * FROM users WHERE username=?", (request.form['username'],), one=True)
        if user and check_password_hash(user['password'], request.form['password']):
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    if session['username'].upper() == 'REUBEN': return redirect(url_for('admin_panel'))
    user = query_db("SELECT * FROM users WHERE username=?", (session['username'],), one=True)
    jobs = query_db("SELECT * FROM jobs WHERE status='live'")
    return render_template('dashboard.html', user=user, jobs=jobs)

@app.route('/pay/<int:job_id>')
def pay_page(job_id):
    job = query_db("SELECT * FROM jobs WHERE id=?", (job_id,), one=True)
    fee = job['salary'] * 0.05
    return render_template('payment.html', job=job, amount=fee)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    res = payments.initiate_mpesa_stk(request.form['phone'], request.form['amount'], request.form['email'], request.form['job_id'])
    if res['success']:
        query_db("INSERT INTO applications (job_id, applicant, payment_status) VALUES (?,?,?)", 
                 (request.form['job_id'], session['username'], 'paid'), commit=True)
    return jsonify(res)

@app.route('/admin_panel')
def admin_panel():
    if session.get('username','').upper() != 'REUBEN': return "Unauthorized", 403
    stats = {'users': len(query_db("SELECT * FROM users")), 'jobs': len(query_db("SELECT * FROM jobs"))}
    return render_template('admin_pannel.html', stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
