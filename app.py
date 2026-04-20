import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from intasend import APIService
from ute import get_ute_math

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'ute_supermax_key_2026')

# Config & IntaSend Integration
DB = "ute.db"
API_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY', '').strip()
API_TOKEN = os.environ.get('INTASEND_API_TOKEN', '').strip()
service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # INITIALIZE DATABASE TABLES
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, email TEXT, phone TEXT, password TEXT, role TEXT, location TEXT, bio_or_company TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, employer TEXT, title TEXT, description TEXT, salary REAL, status TEXT DEFAULT 'open')")
    cur.execute("CREATE TABLE IF NOT EXISTS contracts (id INTEGER PRIMARY KEY AUTOINCREMENT, employer TEXT, employee TEXT, salary REAL, total_months_paid INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS wallet (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
    cur.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, amount REAL, type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    
    cur.execute(query, args)
    rv = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    if 'username' not in session:
        return render_template('landing.html')
    
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    jobs = query_db("SELECT * FROM jobs WHERE status = 'open' ORDER BY id DESC")
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (session['username'],), one=True)
    balance = wallet['balance'] if wallet else 0.0
    
    stats = {
        'total_users': len(query_db("SELECT id FROM users")),
        'active_jobs': len(jobs)
    }
    
    contracts = query_db("SELECT * FROM contracts WHERE employee = ? OR employer = ?", (session['username'], session['username']))
    recent_tx = query_db("SELECT * FROM transactions WHERE sender = ? OR receiver = ? ORDER BY timestamp DESC LIMIT 5", (session['username'], session['username']))
    
    return render_template('dashboard.html', user=user, jobs=jobs, balance=balance, stats=stats, contracts=contracts, recent_tx=recent_tx)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            query_db("INSERT INTO users (username, email, phone, password, role) VALUES (?, ?, ?, ?, ?)", (username, email, phone, hashed, role), commit=True)
            query_db("INSERT INTO wallet (username, balance) VALUES (?, 0.0)", (username,), commit=True)
            return redirect(url_for('login'))
        except: return "Error: User exists or Database Issue."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if user and bcrypt.checkpw(p.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'], session['role'] = user['username'], user['role']
            return redirect(url_for('index'))
        return "Invalid Credentials"
    return render_template('login.html')

@app.route('/post_job', methods=['POST'])
def post_job():
    data = request.json
    query_db("INSERT INTO jobs (employer, title, description, salary) VALUES (?, ?, ?, ?)",
             (session['username'], data['title'], data['description'], data['salary']), commit=True)
    return jsonify({"status": "success"})

@app.route('/pay_contract/<int:id>', methods=['POST'])
def pay_contract(id):
    if session.get('role') not in ['employer', 'admin']: return jsonify({"error": "Unauthorized"}), 403
    c = query_db("SELECT * FROM contracts WHERE id = ?", (id,), one=True)
    e = query_db("SELECT phone FROM users WHERE username = ?", (session['username'],), one=True)
    math = get_ute_math(c['salary'], c['total_months_paid'])
    try:
        service.collect.mpesa_stk_push(phone_number=e['phone'], amount=math['total'], narrative="UTE Salary Pay")
        query_db("UPDATE contracts SET total_months_paid = total_months_paid + 1 WHERE id = ?", (id,), commit=True)
        query_db("UPDATE wallet SET balance = balance + ? WHERE username = ?", (math['net'], c['employee']), commit=True)
        query_db("INSERT INTO transactions (sender, receiver, amount, type) VALUES (?, ?, ?, 'Salary')", (session['username'], c['employee'], math['net']), commit=True)
        return jsonify({"status": "success"})
    except Exception as err: return jsonify({"error": str(err)}), 400

@app.route('/apply/<int:job_id>', methods=['POST'])
def apply(job_id):
    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    query_db("INSERT INTO contracts (employer, employee, salary) VALUES (?, ?, ?)", (job['employer'], session['username'], job['salary']), commit=True)
    query_db("UPDATE jobs SET status = 'closed' WHERE id = ?", (job_id,), commit=True)
    return redirect(url_for('index'))

@app.route('/admin_room')
def admin_room():
    if session.get('role') != 'admin': return "Access Denied", 403
    users = query_db("SELECT * FROM users")
    total_liq = sum(w['balance'] for w in query_db("SELECT balance FROM wallet"))
    return render_template('admin_room.html', users=users, total_liquidity=total_liq)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
