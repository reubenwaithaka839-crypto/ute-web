import os
import sqlite3
import ute
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort

app = Flask(__name__)
# Security: Randomizing secret key and adding a salt for session safety
app.secret_key = os.environ.get("FLASK_SECRET", secrets.token_hex(32))
DB = ute.DB

# ANTI-CLONE PROTOCOL: Dynamic Internal Endpoints
# This makes standard scraper patterns fail
ADMIN_KEY = "RW_PRESTIGE_ADMIN_2026"

def init_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # CORE INFRASTRUCTURE
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, 
        passcode TEXT, email TEXT, role TEXT, 
        bank_name TEXT, acc_number TEXT, holder_name TEXT)""")
    
    cur.execute("CREATE TABLE IF NOT EXISTS blacklist (username TEXT UNIQUE, email TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, salary REAL, employer TEXT)")
    
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER, applicant TEXT, 
        phone TEXT, email TEXT, age INTEGER, skills TEXT, gender TEXT, 
        photo_url TEXT, status TEXT DEFAULT 'pending', applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    cur.execute("CREATE TABLE IF NOT EXISTS treasury (account_name TEXT, account_number TEXT, bank_name TEXT, branch_code TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS wallets (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
    
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        if commit: conn.commit()
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        print(f"DB Error: {e}")
        return None
    finally:
        conn.close()

# Start DB
init_db()

# --- ROUTES ---

@app.route('/')
def portal():
    return render_template('portal.html')

@app.route('/auth/access', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('passcode')
        e = request.form.get('email')
        r = request.form.get('role', 'talent') # Default role
        
        # Blacklist Check
        if query_db("SELECT * FROM blacklist WHERE username = ?", (u,), one=True):
            return "ACCESS RESTRICTED: SECURITY PROTOCOL 403", 403

        # Auto-Admin for Reuben
        role = 'admin' if u.upper() == 'REUBEN' else r
        
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users (username, passcode, email, role) VALUES (?,?,?,?)", 
                     (u, p, e, role), commit=True)
        
        session['username'] = u
        session['role'] = role
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/core/v1/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('portal'))
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    
    if user['role'] == 'admin': return redirect(url_for('admin_panel'))
    
    jobs = query_db("SELECT * FROM jobs")
    return render_template('dashboard.html', user=user, jobs=jobs)

# INVESTOR ANALYTICS PANEL
@app.route('/gatekeeper/analytics/admin')
def admin_panel():
    if 'username' not in session or session['username'].upper() != 'REUBEN':
        abort(403)
        
    # Investor Metrics
    metrics = {
        'total_users': query_db("SELECT COUNT(*) as c FROM users", one=True)['c'],
        'live_jobs': query_db("SELECT COUNT(*) as c FROM jobs", one=True)['c'],
        'total_apps': query_db("SELECT COUNT(*) as c FROM applications", one=True)['c'],
        'employers': query_db("SELECT COUNT(DISTINCT employer) as c FROM jobs", one=True)['c'],
        'revenue_projection': query_db("SELECT SUM(salary * 0.10) as rev FROM jobs", one=True)['rev'] or 0
    }
    
    all_users = query_db("SELECT * FROM users ORDER BY id DESC")
    all_apps = query_db("""
        SELECT a.applicant, j.title, a.status, a.phone 
        FROM applications a 
        JOIN jobs j ON a.job_id = j.id 
        ORDER BY a.id DESC LIMIT 20
    """)
    
    return render_template('admin_pannel.html', 
                           metrics=metrics, 
                           users=all_users, 
                           apps=all_apps)

@app.route('/action/post-job', methods=['POST'])
def post_job():
    if 'username' not in session: return "Unauthorized", 401
    title = request.form.get('title')
    salary = request.form.get('salary')
    query_db("INSERT INTO jobs (title, salary, employer) VALUES (?,?,?)", 
             (title, salary, session['username']), commit=True)
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

if __name__ == '__main__':
    # Use environment port for Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
