import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'PRESTIGE_ULTIMATE_2026_V4')
DB = ute.DB

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # USERS & BANKING
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, 
        passcode TEXT, email TEXT, role TEXT, 
        bank_name TEXT, acc_number TEXT, holder_name TEXT)""")
    
    # SYSTEM CONFIG (For your KRA PIN and Bank Connection)
    cur.execute("""CREATE TABLE IF NOT EXISTS system_config (
        id INTEGER PRIMARY KEY, kra_pin TEXT, bank_status TEXT, 
        api_connection TEXT DEFAULT 'PENDING')""")
    
    # JOBS & APPS
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, salary REAL, employer TEXT)")
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER, applicant TEXT, 
        status TEXT DEFAULT 'pending')""")
    
    # Ensure config row exists
    cur.execute("INSERT OR IGNORE INTO system_config (id, kra_pin, bank_status) VALUES (1, 'NOT_SET', 'DISCONNECTED')")
    
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

init_db()

@app.route('/')
def portal(): return render_template('portal.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username').strip()
        session['username'] = u
        session['role'] = 'admin' if u.upper() == 'REUBEN' else 'user'
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('portal'))
    if session.get('role') == 'admin': return redirect(url_for('admin_panel'))
    jobs = query_db("SELECT * FROM jobs")
    return render_template('dashboard.html', jobs=jobs)

@app.route('/admin_chamber')
def admin_panel():
    if session.get('username','').upper() != 'REUBEN': abort(403)
    
    # INVESTOR ANALYTICS
    total_users = query_db("SELECT COUNT(*) as c FROM users", one=True)['c']
    total_jobs = query_db("SELECT COUNT(*) as c FROM jobs", one=True)['c']
    total_apps = query_db("SELECT COUNT(*) as c FROM applications", one=True)['c']
    total_employers = query_db("SELECT COUNT(DISTINCT employer) as c FROM jobs", one=True)['c']
    
    # KRA & BANK STATUS
    config = query_db("SELECT * FROM system_config WHERE id=1", one=True)
    
    recent_users = query_db("SELECT * FROM users ORDER BY id DESC LIMIT 5")
    
    return render_template('admin_pannel.html', 
                           users_count=total_users, 
                           jobs_count=total_jobs, 
                           apps_count=total_apps, 
                           employers_count=total_employers,
                           config=config,
                           recent_users=recent_users)

@app.route('/update_kra', methods=['POST'])
def update_kra():
    if session.get('username','').upper() != 'REUBEN': abort(403)
    new_pin = request.form.get('kra_pin')
    query_db("UPDATE system_config SET kra_pin=?, bank_status='CONNECTED', api_connection='LIVE' WHERE id=1", (new_pin,), commit=True)
    flash("System Globally Connected to Banking Network!")
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
