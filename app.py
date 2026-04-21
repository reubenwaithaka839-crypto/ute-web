import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from ute import get_ute_math # Assumes your math logic is in ute.py

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supermax_vault_key_999')
DB = "ute_supermax_v5.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Schema with Bank Details
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, email TEXT, phone TEXT, password TEXT, role TEXT, 
        bank_name TEXT, bank_account TEXT
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
        available_jobs = query_db("SELECT * FROM jobs WHERE status = 'open' ORDER BY id DESC")
        return render_template('dashboard.html', user=user, balance=balance, available_jobs=available_jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, e, ph, p, r = request.form.get('username'), request.form.get('email'), request.form.get('phone'), request.form.get('password'), request.form.get('role')
        bn, ba = request.form.get('bank_name'), request.form.get('bank_account')
        hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            query_db("INSERT INTO users (username, email, phone, password, role, bank_name, bank_account) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (u, e, ph, hashed, r, bn, ba), commit=True)
            query_db("INSERT INTO wallet (username, balance) VALUES (?, 0.0)", (u,), commit=True)
            return redirect(url_for('login'))
        except: return "Registration Error: Check if username exists."
    return render_template('register.html')

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'username' not in session: return redirect(url_for('login'))
    gross_amount = float(request.form.get('amount'))
    user = session['username']
    
    # CALCULATE UTE DEDUCTIONS
    # get_ute_math(amount) should return a dict: {'deduction': x, 'net': y}
    math = get_ute_math(gross_amount) 
    deduction = math['deduction']
    net_to_bank = math['net']

    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (user,), one=True)
    if wallet and wallet['balance'] >= gross_amount:
        # Deduct gross from wallet
        query_db("UPDATE wallet SET balance = balance - ? WHERE username = ?", (gross_amount, user), commit=True)
        # Log pending transaction for Admin approval
        query_db("""INSERT INTO transactions (sender, receiver, amount, deduction, net_amount, type, status) 
                    VALUES (?, 'BANK_SETTLEMENT', ?, ?, ?, 'Withdrawal', 'pending')""", 
                 (user, gross_amount, deduction, net_to_bank), commit=True)
        return redirect(url_for('index'))
    return "Insufficient balance."

@app.route('/admin_room')
def admin_room():
    if session.get('role') != 'admin': return "Unauthorized", 403
    withdrawals = query_db("""SELECT transactions.*, users.bank_name, users.bank_account 
                              FROM transactions 
                              JOIN users ON transactions.sender = users.username 
                              WHERE transactions.status = 'pending'""")
    return render_template('admin_room.html', withdrawals=withdrawals)

@app.route('/approve_transfer/<int:id>', methods=['POST'])
def approve_transfer(id):
    if session.get('role') != 'admin': return "Unauthorized", 403
    query_db("UPDATE transactions SET status = 'completed' WHERE id = ?", (id,), commit=True)
    return redirect(url_for('admin_room'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if user and bcrypt.checkpw(p.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'], session['role'] = user['username'], user['role']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
