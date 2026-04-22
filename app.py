import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'RW_ULTIMATE_GOD_KEY_2026'
DB = ute.DB

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # MASTER ARCHITECTURE BOOTSTRAP
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, 
        passcode TEXT, 
        email TEXT, 
        role TEXT
    )""")
    cur.execute("CREATE TABLE IF NOT EXISTS blacklist (username TEXT UNIQUE, email TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, posted_by TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS treasury (
        account_name TEXT, 
        account_number TEXT, 
        bank_name TEXT, 
        branch_code TEXT
    )""")
    
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/portal')
def portal():
    return render_template('portal.html')

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('portal'))
    if not session.get('terms_accepted'): return redirect(url_for('terms'))
    
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    if not user: 
        session.clear()
        return redirect(url_for('portal'))
        
    if user['role'] == 'admin': return redirect(url_for('admin_panel'))
    return render_template('dashboard.html', user=user)

@app.route('/terms', methods=['GET', 'POST'])
def terms():
    if request.method == 'POST':
        session['terms_accepted'] = True
        return redirect(url_for('index'))
    return render_template('terms.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('passcode')
        e = request.form.get('email')
        r = request.form.get('role', 'employee')
        
        is_banned = query_db("SELECT * FROM blacklist WHERE username = ? OR email = ?", (u, e), one=True)
        if is_banned: return "IDENTITY DISMANTLED: Access Denied Forever.", 403
        
        # MASTER OVERRIDE FOR REUBEN
        role = 'admin' if u.upper() == 'REUBEN' else r
        
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users (username, passcode, email, role) VALUES (?, ?, ?, ?)", (u, p, e, role), commit=True)
        
        session['username'] = u
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session['username'].upper() != 'REUBEN':
        return "UNAUTHORIZED: Master Admin Only", 403
        
    all_users = query_db("SELECT * FROM users")
    job_count = query_db("SELECT COUNT(*) as count FROM jobs", one=True)
    treasury = query_db("SELECT * FROM treasury", one=True)
    
    return render_template('admin_pannel.html', 
                           all_users=all_users, 
                           job_count=job_count['count'] if job_count else 0, 
                           treasury=treasury)

@app.route('/update_treasury', methods=['POST'])
def update_treasury():
    if 'username' not in session or session['username'].upper() != 'REUBEN': return "UNAUTHORIZED", 403
    name = request.form.get('acc_name')
    num = request.form.get('acc_num')
    bank = request.form.get('bank')
    branch = request.form.get('branch')
    
    query_db("DELETE FROM treasury", commit=True)
    query_db("INSERT INTO treasury (account_name, account_number, bank_name, branch_code) VALUES (?, ?, ?, ?)", 
             (name, num, bank, branch), commit=True)
    return redirect(url_for('admin_panel'))

@app.route('/register_admin', methods=['POST'])
def register_admin():
    if 'username' not in session or session['username'].upper() != 'REUBEN': return "UNAUTHORIZED", 403
    u = request.form.get('username')
    p = request.form.get('passcode')
    e = request.form.get('email')
    
    try:
        query_db("INSERT INTO users (username, passcode, email, role) VALUES (?, ?, ?, 'admin')", (u, p, e), commit=True)
    except:
        pass # User likely already exists
    return redirect(url_for('admin_panel'))

@app.route('/dismantle_admin/<username>')
def dismantle_admin(username):
    if 'username' not in session or session['username'].upper() != 'REUBEN': return "UNAUTHORIZED", 403
    if username.upper() == 'REUBEN': return "CANNOT DISMANTLE MASTER", 403
    
    target = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
    if target:
        query_db("INSERT INTO blacklist (username, email) VALUES (?, ?)", (target['username'], target['email']), commit=True)
        query_db("DELETE FROM users WHERE username = ?", (username,), commit=True)
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
