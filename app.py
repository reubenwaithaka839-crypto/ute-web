import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
# Security Key for Sessions
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supermax_vault_key_999')

# Database Name
DB = "ute_supermax_v3.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Ensure all tables exist with correct columns
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, email TEXT, phone TEXT, password TEXT, role TEXT, 
        bank_name TEXT, bank_account TEXT
    )""")
    cur.execute("CREATE TABLE IF NOT EXISTS wallet (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        sender TEXT, receiver TEXT, amount REAL, type TEXT, 
        status TEXT DEFAULT 'completed', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employer TEXT, title TEXT, description TEXT, salary REAL, status TEXT DEFAULT 'open'
    )""")
    cur.execute(query, args)
    rv = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# --- ROUTES ---

@app.route('/')
def index():
    if 'username' in session:
        user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
        wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (session['username'],), one=True)
        balance = wallet['balance'] if wallet else 0.0
        # Load Jobs for the dashboard
        jobs = query_db("SELECT * FROM jobs WHERE status = 'open' ORDER BY id DESC")
        return render_template('dashboard.html', user=user, balance=balance, jobs=jobs)
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('username')
        e = request.form.get('email')
        ph = request.form.get('phone')
        p = request.form.get('password')
        r = request.form.get('role')
        hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            query_db("INSERT INTO users (username, email, phone, password, role) VALUES (?, ?, ?, ?, ?)", 
                     (u, e, ph, hashed, r), commit=True)
            query_db("INSERT INTO wallet (username, balance) VALUES (?, 0.0)", (u,), commit=True)
            return redirect(url_for('login'))
        except:
            return "Registration Error: User might already exist."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if user and bcrypt.checkpw(p.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        return "Invalid Credentials"
    return render_template('login.html')

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'username' not in session: return redirect(url_for('login'))
    amount = float(request.form.get('amount'))
    user = session['username']
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (user,), one=True)
    if wallet and wallet['balance'] >= amount:
        query_db("UPDATE wallet SET balance = balance - ? WHERE username = ?", (amount, user), commit=True)
        query_db("INSERT INTO transactions (sender, receiver, amount, type, status) VALUES (?, 'BANK_SYSTEM', ?, 'Withdrawal Request', 'pending')", 
                 (user, amount), commit=True)
    return redirect(url_for('index'))

@app.route('/admin')
@app.route('/admin_room')
@app.route('/admin_panel')
def admin_room():
    if session.get('role') != 'admin': return "Unauthorized Access", 403
    withdrawals = query_db("SELECT * FROM transactions WHERE type = 'Withdrawal Request' AND status = 'pending'")
    jobs = query_db("SELECT * FROM jobs ORDER BY id DESC")
    return render_template('admin_room.html', withdrawals=withdrawals, jobs=jobs)

@app.route('/post_job', methods=['POST'])
def post_job():
    if session.get('role') != 'admin': return "Unauthorized", 403
    title = request.form.get('title')
    desc = request.form.get('description')
    sal = request.form.get('salary')
    emp = request.form.get('employer')
    query_db("INSERT INTO jobs (title, description, salary, employer) VALUES (?, ?, ?, ?)", 
             (title, desc, sal, emp), commit=True)
    return redirect(url_for('admin_room'))

@app.route('/approve_withdrawal/<int:id>', methods=['POST'])
def approve_withdrawal(id):
    if session.get('role') != 'admin': return "Unauthorized", 403
    query_db("UPDATE transactions SET status = 'completed' WHERE id = ?", (id,), commit=True)
    return redirect(url_for('admin_room'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
