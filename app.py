import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from intasend import APIService
from ute import get_ute_math

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supermax_bank_777')

DB = "ute.db"
API_PUBLISHABLE_KEY = os.environ.get('INTASEND_PUBLISHABLE_KEY', '').strip()
API_TOKEN = os.environ.get('INTASEND_API_TOKEN', '').strip()
service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, email TEXT, phone TEXT, password TEXT, role TEXT, 
        location TEXT, bio_or_company TEXT, 
        bank_name TEXT, bank_account TEXT
    )""")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, employer TEXT, title TEXT, description TEXT, salary REAL, status TEXT DEFAULT 'open')")
    cur.execute("CREATE TABLE IF NOT EXISTS contracts (id INTEGER PRIMARY KEY AUTOINCREMENT, employer TEXT, employee TEXT, salary REAL, total_months_paid INTEGER DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS wallet (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        sender TEXT, receiver TEXT, amount REAL, type TEXT, 
        status TEXT DEFAULT 'completed', timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute(query, args)
    rv = cur.fetchall()
    if commit: conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('login'))
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    jobs = query_db("SELECT * FROM jobs WHERE status = 'open' ORDER BY id DESC")
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (session['username'],), one=True)
    balance = wallet['balance'] if wallet else 0.0
    stats = {'total_users': len(query_db("SELECT id FROM users")), 'active_jobs': len(jobs)}
    contracts = query_db("SELECT * FROM contracts WHERE employee = ? OR employer = ?", (session['username'], session['username']))
    recent_tx = query_db("SELECT * FROM transactions WHERE sender = ? OR receiver = ? ORDER BY timestamp DESC LIMIT 5", (session['username'], session['username']))
    return render_template('dashboard.html', user=user, jobs=jobs, balance=balance, stats=stats, contracts=contracts, recent_tx=recent_tx)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if user and bcrypt.checkpw(p.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'], session['role'] = user['username'], user['role']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/withdraw', methods=['POST'])
def withdraw():
    amount = float(request.form.get('amount'))
    user = session['username']
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (user,), one=True)
    if wallet and wallet['balance'] >= amount:
        query_db("UPDATE wallet SET balance = balance - ? WHERE username = ?", (amount, user), commit=True)
        query_db("INSERT INTO transactions (sender, receiver, amount, type, status) VALUES (?, 'BANK', ?, 'Withdrawal Request', 'pending')", 
                 (user, amount), commit=True)
    return redirect(url_for('index'))

@app.route('/admin_room')
def admin_room():
    if session.get('role') != 'admin': return "Unauthorized", 403
    users = query_db("SELECT * @FROM users")
    withdrawals = query_db("SELECT * FROM transactions WHERE type = 'Withdrawal Request' AND status = 'pending'")
    total_liq = sum(w['balance'] for w in query_db("SELECT balance FROM wallet"))
    return render_template('admin_room.html', users=users, total_liquidity=total_liq, withdrawals=withdrawals)

@app.route('/approve_withdrawal/<int:id>', methods=['POST'])
def approve_withdrawal(id):
    if session.get('role') != 'admin': return "Unauthorized", 403
    query_db("UPDATE transactions SET status = 'completed' WHERE id = ?", (id,), commit=True)
    return redirect(url_for('admin_room'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
