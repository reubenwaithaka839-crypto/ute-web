import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session
from ute import get_ute_math

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'reubbie@janny112008_vault')

# Brand new DB name for a fresh, clean start
DB = "ute_supermax_FINAL_BOSS.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, email TEXT, phone TEXT, password TEXT, role TEXT, 
        bank_name TEXT, bank_account TEXT, status TEXT DEFAULT 'active'
    )""")
    cur.execute("CREATE TABLE IF NOT EXISTS wallet (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        sender TEXT, receiver TEXT, amount REAL, deduction REAL, 
        net_amount REAL, type TEXT, status TEXT DEFAULT 'completed', 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employer TEXT, title TEXT, description TEXT, 
        salary REAL, location TEXT, skills TEXT, status TEXT DEFAULT 'open'
    )""")
    cur.execute(query, args)
    rv = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    if 'username' not in session: return render_template('landing.html')
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (session['username'],), one=True)
    balance = wallet['balance'] if wallet else 0.0
    
    if user['role'] == 'employer':
        my_jobs = query_db("SELECT * FROM jobs WHERE employer = ? ORDER BY id DESC", (user['username'],))
        return render_template('dashboard.html', user=user, balance=balance, my_jobs=my_jobs)
    else:
        search = request.args.get('search', '')
        available_jobs = query_db("SELECT * FROM jobs WHERE status = 'open' AND (title LIKE ? OR location LIKE ?)", ('%'+search+'%', '%'+search+'%'))
        return render_template('dashboard.html', user=user, balance=balance, available_jobs=available_jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, e, ph, p, r = request.form.get('username'), request.form.get('email'), request.form.get('phone'), request.form.get('password'), request.form.get('role')
        bn, ba = request.form.get('bank_name'), request.form.get('bank_account')
        
        # ROOT BOSS SECURITY: REUBEN is always active. Others must be approved.
        if u.upper() == 'REUBEN':
            status = 'active'
        else:
            status = 'pending_approval' if r == 'admin' else 'active'
        
        hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            query_db("""INSERT INTO users (username, email, phone, password, role, bank_name, bank_account, status) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (u, e, ph, hashed, r, bn, ba, status), commit=True)
            query_db("INSERT INTO wallet (username, balance) VALUES (?, 0.0)", (u,), commit=True)
            return redirect(url_for('login'))
        except: return "Error: Username Taken"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if user and bcrypt.checkpw(p.encode('utf-8'), user['password'].encode('utf-8')):
            if u.upper() != 'REUBEN' and user['status'] == 'pending_approval':
                return "<h1>Access Pending</h1><p>Wait for REUBEN to approve your access.</p>"
            session['username'], session['role'], session['user_id'] = user['username'], user['role'], user['id']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin_room')
def admin_room():
    if session.get('role') != 'admin': return "Unauthorized", 403
    withdrawals = query_db("""SELECT transactions.*, users.bank_name, users.bank_account 
                              FROM transactions JOIN users ON transactions.sender = users.username 
                              WHERE transactions.status = 'pending'""")
    pending_admins = []
    # ONLY REUBEN (The Master) can see the approval list
    if session.get('username').upper() == 'REUBEN':
        pending_admins = query_db("SELECT * FROM users WHERE role = 'admin' AND status = 'pending_approval'")
    return render_template('admin_room.html', withdrawals=withdrawals, pending_admins=pending_admins)

@app.route('/approve_admin/<int:id>')
def approve_admin(id):
    if session.get('username').upper() != 'REUBEN': return "Denied", 403
    query_db("UPDATE users SET status = 'active' WHERE id = ?", (id,), commit=True)
    return redirect(url_for('admin_room'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
