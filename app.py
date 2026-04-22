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
    # PRESTIGE DATABASE ARCHITECTURE
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, passcode TEXT, email TEXT, phone TEXT, role TEXT, photo_url TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, location TEXT, salary REAL, posted_by TEXT, skills_required TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS blacklist (username TEXT UNIQUE, email TEXT UNIQUE)")
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER, applicant_username TEXT,
        full_name TEXT, id_number TEXT, phone TEXT, email TEXT, gender TEXT, 
        age INTEGER, location TEXT, skills TEXT, photo_url TEXT, status TEXT DEFAULT 'pending'
    )""")
    cur.execute(query, args)
    if commit: conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('login'))
    if not session.get('terms_accepted'): return redirect(url_for('terms'))
    
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    if not user:
        session.clear()
        return redirect(url_for('login'))
        
    jobs = query_db("SELECT * FROM jobs ORDER BY id DESC")
    all_users = query_db("SELECT * FROM users") if user['role'] == 'admin' else []
    
    return render_template('dashboard.html', user=user, jobs=jobs, all_users=all_users)

@app.route('/terms', methods=['GET', 'POST'])
def terms():
    if request.method == 'POST':
        session['terms_accepted'] = True
        return redirect(url_for('index'))
    return render_template('terms.html')

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session['username'].upper() != 'REUBEN':
        return "ACCESS DENIED: Master Admin Clearance Required", 403
    
    all_users = query_db("SELECT * FROM users")
    all_jobs = query_db("SELECT * FROM jobs")
    all_apps = query_db("SELECT a.*, j.title as job_title FROM applications a JOIN jobs j ON a.job_id = j.id")
    return render_template('admin_pannel.html', all_users=all_users, all_jobs=all_jobs, all_apps=all_apps)

@app.route('/register_admin', methods=['POST'])
def register_admin():
    if 'username' not in session or session['username'].upper() != 'REUBEN': return "UNAUTHORIZED", 403
    u, p, e, ph = request.form.get('username'), request.form.get('passcode'), request.form.get('email'), request.form.get('phone')
    
    is_banned = query_db("SELECT * FROM blacklist WHERE username = ? OR email = ?", (u, e), one=True)
    if is_banned: return "PROTOCOL ERROR: Identity is Blacklisted", 403

    query_db("INSERT INTO users (username, passcode, email, phone, role) VALUES (?, ?, ?, ?, 'admin')", (u, p, e, ph), commit=True)
    return redirect(url_for('admin_panel'))

@app.route('/dismantle_admin/<username>')
def dismantle_admin(username):
    if 'username' not in session or session['username'].upper() != 'REUBEN': return "UNAUTHORIZED", 403
    if username.upper() == 'REUBEN': return "IMMORTAL STATUS: Cannot dismantle self", 403
    
    target = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
    if target:
        query_db("INSERT INTO blacklist (username, email) VALUES (?, ?)", (target['username'], target['email']), commit=True)
        query_db("DELETE FROM users WHERE username = ?", (username,), commit=True)
    return redirect(url_for('admin_panel'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p, e, r = request.form.get('username'), request.form.get('passcode'), request.form.get('email'), request.form.get('role', 'employee')
        
        is_banned = query_db("SELECT * FROM blacklist WHERE username = ? OR email = ?", (u, e), one=True)
        if is_banned: return "SYSTEM ERROR: Identity Dismantled. Access Revoked.", 403
        
        role = 'admin' if u.upper() == 'REUBEN' else r
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users (username, passcode, email, role) VALUES (?, ?, ?, ?)", (u, p, e, role), commit=True)
        session['username'] = u
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
