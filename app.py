import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session
from ute import get_ute_math

app = Flask(__name__)
# Secure secret key for sessions
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'supermax_vault_alpha_777_final')

# DATABASE NAME: Updated to v1 to force a fresh start on Render
DB = "ute_supermax_final_v1.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # 1. USERS TABLE (Includes Bank & Approval Status)
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, email TEXT, phone TEXT, password TEXT, role TEXT, 
        bank_name TEXT, bank_account TEXT, status TEXT DEFAULT 'active'
    )""")
    
    # 2. WALLET TABLE
    cur.execute("CREATE TABLE IF NOT EXISTS wallet (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
    
    # 3. TRANSACTIONS TABLE (Includes UTE Deductions)
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        sender TEXT, receiver TEXT, amount REAL, deduction REAL, 
        net_amount REAL, type TEXT, status TEXT DEFAULT 'completed', 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # 4. JOBS TABLE (Includes Location & Skills)
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
        # Employee view with search functionality
        search = request.args.get('search', '')
        if search:
            available_jobs = query_db("""SELECT * FROM jobs WHERE status = 'open' 
                                      AND (title LIKE ? OR location LIKE ? OR skills LIKE ?)""", 
                                    ('%'+search+'%', '%'+search+'%', '%'+search+'%'))
        else:
            available_jobs = query_db("SELECT * FROM jobs WHERE status = 'open' ORDER BY id DESC")
        return render_template('dashboard.html', user=user, balance=balance, available_jobs=available_jobs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form.get('username')
        e = request.form.get('email')
        ph = request.form.get('phone')
        p = request.form.get('password')
        r = request.form.get('role')
        bn = request.form.get('bank_name')
        ba = request.form.get('bank_account')
        
        # LOGIC: New Admins are locked until approved
        status = 'pending_approval' if r == 'admin' else 'active'
        
        hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            query_db("""INSERT INTO users (username, email, phone, password, role, bank_name, bank_account, status) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                     (u, e, ph, hashed, r, bn, ba, status), commit=True)
            query_db("INSERT INTO wallet (username, balance) VALUES (?, 0.0)", (u,), commit=True)
            return redirect(url_for('login'))
        except:
            return "Registration Error: Username may be taken."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if user and bcrypt.checkpw(p.encode('utf-8'), user['password'].encode('utf-8')):
            if user['status'] == 'pending_approval':
                return "<h1>Access Pending</h1><p>Your Admin account must be authorized by User ID 1.</p>"
            
            session['username'], session['role'], session['user_id'] = user['username'], user['role'], user['id']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin_room')
def admin_room():
    if session.get('role') != 'admin': return "Unauthorized", 403
    
    # Settlements list
    withdrawals = query_db("""SELECT transactions.*, users.bank_name, users.bank_account 
                              FROM transactions JOIN users ON transactions.sender = users.username 
                              WHERE transactions.status = 'pending'""")
    
    # Admin Approval Queue (ONLY for Super Admin ID 1)
    pending_admins = []
    if session.get('user_id') == 1:
        pending_admins = query_db("SELECT * FROM users WHERE role = 'admin' AND status = 'pending_approval'")
    
    return render_template('admin_room.html', withdrawals=withdrawals, pending_admins=pending_admins)

@app.route('/approve_admin/<int:id>')
def approve_admin(id):
    if session.get('user_id') != 1: return "Unauthorized", 403
    
    # Check current admin count (Limit to 3)
    active_admins = query_db("SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND status = 'active'", one=True)['count']
    if active_admins >= 3:
        return "<h1>Limit Reached</h1><p>Only 3 active Admins are allowed.</p>"
    
    query_db("UPDATE users SET status = 'active' WHERE id = ?", (id,), commit=True)
    return redirect(url_for('admin_room'))

@app.route('/withdraw', methods=['POST'])
def withdraw():
    if 'username' not in session: return redirect(url_for('login'))
    
    gross_amount = float(request.form.get('amount'))
    math = get_ute_math(gross_amount)
    user = session['username']
    
    wallet = query_db("SELECT balance FROM wallet WHERE username = ?", (user,), one=True)
    if wallet and wallet['balance'] >= gross_amount:
        query_db("UPDATE wallet SET balance = balance - ? WHERE username = ?", (gross_amount, user), commit=True)
        query_db("""INSERT INTO transactions (sender, receiver, amount, deduction, net_amount, type, status) 
                    VALUES (?, 'BANK_SETTLEMENT', ?, ?, ?, 'Withdrawal', 'pending')""", 
                 (user, gross_amount, math['deduction'], math['net']), commit=True)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
