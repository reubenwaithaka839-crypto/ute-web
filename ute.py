import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'RW_ULTIMATE_PRESTIGE_2026_SECURE_V3_XYZ'
DB = ute.DB

def init_db():
    """RW Prestige Secure Database Bootstrap"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE NOT NULL,
        passcode TEXT NOT NULL, 
        email TEXT UNIQUE,
        role TEXT DEFAULT 'user',
        bank_name TEXT,
        acc_number TEXT,
        holder_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("CREATE TABLE IF NOT EXISTS blacklist (username TEXT UNIQUE, email TEXT UNIQUE, reason TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, salary REAL, employer TEXT, description TEXT, status TEXT DEFAULT 'live', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        job_id INTEGER, 
        applicant TEXT, 
        phone TEXT, 
        email TEXT, 
        age INTEGER, 
        skills TEXT, 
        gender TEXT, 
        photo_url TEXT, 
        status TEXT DEFAULT 'pending',
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("CREATE TABLE IF NOT EXISTS treasury (account_name TEXT, account_number TEXT, bank_name TEXT, branch_code TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cur.execute("CREATE TABLE IF NOT EXISTS wallet (username TEXT PRIMARY KEY, balance REAL DEFAULT 0.0)")
    cur.execute("CREATE TABLE IF NOT EXISTS contracts (id INTEGER PRIMARY KEY AUTOINCREMENT, employer TEXT, employee TEXT, salary REAL, total_months_paid INTEGER DEFAULT 0)")
        
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False, commit=False):
    """Secure RW Database Query Engine"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        if commit: conn.commit()
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        print(f"🔒 DB Error: {e}")
        return None if one else []
    finally:
        conn.close()

init_db()

@app.route('/')
def portal():
    return render_template('portal.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('passcode')
        e = request.form.get('email')
        r = request.form.get('role', 'user')
        
        # Admin Override logic
        final_role = 'admin' if u.upper() == 'REUBEN' else r
        
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users (username, passcode, email, role, bank_name, acc_number, holder_name) VALUES (?,?,?,?,?,?,?)", 
                     (u, p, e, final_role, request.form.get('bank_name'), request.form.get('acc_num'), request.form.get('holder')), commit=True)
        
        session['username'] = u
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('portal'))
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    if not user: return redirect(url_for('logout'))
    if user['role'] == 'admin' or user['username'].upper() == 'REUBEN': return redirect(url_for('admin_panel'))
    
    jobs = query_db("SELECT * FROM jobs WHERE status='live'")
    return render_template('dashboard.html', user=user, jobs=jobs)

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session['username'].upper() != 'REUBEN':
        return "🚫 UNAUTHORIZED", 403
        
    stats = {
        'total_users': query_db("SELECT COUNT(*) as count FROM users", one=True)['count'],
        'live_jobs': query_db("SELECT COUNT(*) as count FROM jobs WHERE status='live'", one=True)['count'],
        'total_applications': query_db("SELECT COUNT(*) as count FROM applications", one=True)['count'],
        'total_employers': query_db("SELECT COUNT(*) as count FROM users WHERE role='employer' OR bank_name IS NOT NULL", one=True)['count'],
        'total_wallet': query_db("SELECT COALESCE(SUM(balance), 0) as total FROM wallet", one=True)['total']
    }
    
    recent = {
        'users': query_db("SELECT username, email, role, created_at FROM users ORDER BY id DESC LIMIT 10"),
        'jobs': query_db("SELECT title, salary, employer FROM jobs ORDER BY id DESC LIMIT 5"),
        'apps': query_db("SELECT a.applicant, j.title, a.status FROM applications a JOIN jobs j ON a.job_id=j.id ORDER BY a.id DESC LIMIT 10")
    }
    
    tr = query_db("SELECT * FROM treasury ORDER BY updated_at DESC LIMIT 1", one=True)
    return render_template('admin_pannel.html', stats=stats, recent=recent, treasury=tr)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'username' not in session: return redirect(url_for('portal'))
    if request.method == 'POST':
        query_db("INSERT INTO jobs (title, salary, employer, description) VALUES (?,?,?,?)",
                (request.form['title'], float(request.form['salary']), session['username'], request.form.get('description')), commit=True)
        flash("Job Posted!")
        return redirect(url_for('dashboard'))
    return render_template('post_job.html')

@app.route('/update_treasury', methods=['POST'])
def update_treasury():
    if session.get('username','').upper() != 'REUBEN': return "UNAUTHORIZED", 403
    query_db("INSERT INTO treasury (account_name, account_number, bank_name, branch_code) VALUES (?,?,?,?)", 
             (request.form.get('acc_name'), request.form.get('acc_num'), request.form.get('bank'), request.form.get('branch')), commit=True)
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
