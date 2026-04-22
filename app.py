import os
import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'RW_ULTIMATE_PRESTIGE_2026_SECURE'
DB = ute.DB

def init_db():
    """Builds the core infrastructure on boot"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Table Definitions
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT UNIQUE, 
        passcode TEXT, 
        email TEXT, 
        role TEXT, 
        bank_name TEXT, 
        acc_number TEXT, 
        holder_name TEXT)""")
        
    cur.execute("CREATE TABLE IF NOT EXISTS blacklist (username TEXT UNIQUE, email TEXT UNIQUE)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, salary REAL, employer TEXT)")
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
        status TEXT DEFAULT 'pending')""")
    cur.execute("CREATE TABLE IF NOT EXISTS treasury (account_name TEXT, account_number TEXT, bank_name TEXT, branch_code TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS wallet (username TEXT PRIMARY KEY, balance REAL DEFAULT 0)")
    cur.execute("CREATE TABLE IF NOT EXISTS contracts (id INTEGER PRIMARY KEY AUTOINCREMENT, employer TEXT, employee TEXT, salary REAL, total_months_paid INTEGER DEFAULT 0)")
        
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False, commit=False):
    """Secure Database Interface"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        if commit: conn.commit()
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        print(f"DB Snag: {e}")
        return None if one else []
    finally:
        conn.close()

# Run infrastructure check
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
        r = request.form.get('role')
        b_name = request.form.get('bank_name')
        b_acc = request.form.get('acc_num')
        b_hold = request.form.get('holder')
        
        is_banned = query_db("SELECT * FROM blacklist WHERE username = ? OR email = ?", (u, e), one=True)
        if is_banned: 
            return "IDENTITY DISMANTLED: ACCESS DENIED", 403
        
        # Admin Lock
        role = 'admin' if u.upper() == 'REUBEN' else r
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users VALUES (NULL,?,?,?,?,?,?,?)", 
                     (u, p, e, role or 'user', b_name, b_acc, b_hold), commit=True)
        
        session['username'] = u
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('portal'))
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    if not user: return redirect(url_for('logout'))
    
    if user['role'] == 'admin': return redirect(url_for('admin_panel'))
    
    jobs = query_db("SELECT * FROM jobs")
    if not jobs:
        query_db("INSERT INTO jobs (title, salary, employer) VALUES (?,?,?)", 
                 ("Lead Developer", 185000, "RW Systems"), commit=True)
        jobs = query_db("SELECT * FROM jobs")
        
    return render_template('dashboard.html', user=user, jobs=jobs)

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session['username'].upper() != 'REUBEN': 
        return "UNAUTHORIZED", 403
        
    # --- STATISTICS GATHERING ---
    stats = {
        'total_users': query_db("SELECT COUNT(*) as count FROM users", one=True)['count'],
        'live_jobs': query_db("SELECT COUNT(*) as count FROM jobs", one=True)['count'],
        'total_apps': query_db("SELECT COUNT(*) as count FROM applications", one=True)['count'],
        'total_employers': query_db("""
            SELECT COUNT(*) as count FROM users 
            WHERE role='employer' OR (bank_name IS NOT NULL AND acc_number IS NOT NULL)
        """, one=True)['count']
    }
    
    recent_users = query_db("SELECT username, email, role FROM users ORDER BY id DESC LIMIT 10")
    recent_jobs = query_db("SELECT title, salary, employer FROM jobs ORDER BY id DESC LIMIT 5")
    recent_apps = query_db("""
        SELECT a.applicant, j.title as job_title, a.status 
        FROM applications a 
        JOIN jobs j ON a.job_id = j.id 
        ORDER BY a.id DESC LIMIT 10
    """)
    tr = query_db("SELECT * FROM treasury", one=True)
    
    return render_template('admin_pannel.html', 
                          stats=stats,
                          recent_users=recent_users, 
                          recent_jobs=recent_jobs, 
                          recent_apps=recent_apps, 
                          treasury=tr)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'username' not in session: return redirect(url_for('portal'))
    user = query_db("SELECT role FROM users WHERE username=?", (session['username'],), one=True)
    
    if user['role'] not in ['employer', 'admin']:
        flash("Unauthorized to post jobs.")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        query_db("INSERT INTO jobs (title, salary, employer) VALUES (?,?,?)",
                (request.form['title'], float(request.form['salary']), session['username']), commit=True)
        flash("Job successfully deployed.")
        return redirect(url_for('dashboard'))
    return render_template('post_job.html')

@app.route('/update_treasury', methods=['POST'])
def update_treasury():
    if session.get('username','').upper() != 'REUBEN': return "UNAUTHORIZED", 403
    query_db("DELETE FROM treasury", commit=True)
    query_db("INSERT INTO treasury VALUES (?,?,?,?)", 
             (request.form.get('acc_name'), request.form.get('acc_num'), 
              request.form.get('bank'), request.form.get('branch')), commit=True)
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
