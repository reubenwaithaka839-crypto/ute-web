import os
import sqlite3
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session
from ute import get_ute_math

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'reubbie_ultimate_vault_2026_v4')

# Using V5 to ensure a fresh, bug-free start
DB = "ute_supermax_FINAL_BOSS_V5.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # Create Tables
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, email TEXT, password TEXT, role TEXT, 
        bank_name TEXT, bank_account TEXT, status TEXT DEFAULT 'active'
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        sender TEXT, amount REAL, deduction REAL, 
        net_amount REAL, status TEXT DEFAULT 'pending'
    )""")
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    if 'username' not in session: return render_template('landing.html')
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    # If it's you (Reuben/Admin), go straight to the command center
    if user and user['role'] == 'admin': return redirect(url_for('admin_room'))
    return render_template('dashboard.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, e, p, r = request.form.get('username'), request.form.get('email'), request.form.get('password'), request.form.get('role')
        bn, ba = request.form.get('bank_name'), request.form.get('bank_account')
        
        # Hard Lock: Only Reuben can be the first Admin
        if r == 'admin' and u.upper() != 'REUBEN': 
            return "<h1>Denied</h1><p>Only Reuben can appoint Admins.</p>"
            
        hashed = bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            query_db("INSERT INTO users (username, email, password, role, bank_name, bank_account) VALUES (?, ?, ?, ?, ?, ?)", 
                     (u, e, hashed, r, bn, ba), commit=True)
            return redirect(url_for('login'))
        except: return "Username Taken"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username'), request.form.get('password')
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if user and bcrypt.checkpw(p.encode('utf-8'), user['password'].encode('utf-8')):
            session['username'], session['role'] = user['username'], user['role']
            session['bank_name'], session['bank_account'] = user['bank_name'], user['bank_account']
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin_room')
def admin_room():
    if session.get('role') != 'admin': return "Unauthorized", 403
    all_users = query_db("SELECT * FROM users ORDER BY id DESC")
    return render_template('admin_room.html', all_users=all_users)

@app.route('/update_treasury', methods=['POST'])
def update_treasury():
    if session.get('username').upper() != 'REUBEN': return "Denied", 403
    bn, ba = request.form.get('bank_name'), request.form.get('bank_account')
    query_db("UPDATE users SET bank_name = ?, bank_account = ? WHERE username = ?", (bn, ba, session['username']), commit=True)
    session['bank_name'], session['bank_account'] = bn, ba
    return redirect(url_for('admin_room'))

@app.route('/admin/delete_user/<int:id>')
def delete_user(id):
    if session.get('username').upper() != 'REUBEN': return "Denied", 403
    query_db("DELETE FROM users WHERE id = ?", (id,), commit=True)
    return redirect(url_for('admin_room'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
