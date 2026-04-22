import sqlite3
import ute
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'RW_ULTIMATE_PRESTIGE_2026_SECURE'
DB = ute.DB

def init_db():
    """Initialize database tables once at startup"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Create tables
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
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        if commit: 
            conn.commit()
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        print(f"Database error: {e}")
        return None if one else []
    finally:
        conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def portal():
    return render_template('portal.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username').strip()
        p = request.form.get('passcode')
        e = request.form.get('email')
        r = request.form.get('role')
        b_name = request.form.get('bank_name')
        b_acc = request.form.get('acc_num')
        b_hold = request.form.get('holder')
        
        # Check blacklist
        is_banned = query_db("SELECT * FROM blacklist WHERE username = ? OR email = ?", (u, e), one=True)
        if is_banned: 
            flash("IDENTITY DISMANTLED: ACCESS DENIED")
            return render_template('login.html')
        
        # Check existing user
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users VALUES (NULL,?,?,?,?,?,?,?)", 
                    (u, p, e, r or 'user', b_name, b_acc, b_hold), commit=True)
            flash("Account created successfully!")
        
        session['username'] = u
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: 
        return redirect(url_for('portal'))
    
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    if not user: 
        return redirect(url_for('logout'))
    
    if user['role'] == 'admin': 
        return redirect(url_for('admin_panel'))
    
    jobs = query_db("SELECT * FROM jobs")
    if not jobs:
        query_db("INSERT INTO jobs (title, salary, employer) VALUES (?,?,?)", 
                ("Lead Developer", 185000, "RW Systems"), commit=True)
        jobs = query_db("SELECT * FROM jobs")
    
    return render_template('dashboard.html', user=user, jobs=jobs)

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply(job_id):
    if 'username' not in session: 
        return redirect(url_for('portal'))
    
    job = query_db("SELECT * FROM jobs WHERE id = ?", (job_id,), one=True)
    if not job:
        flash("Job not found")
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = (
            job_id, 
            session['username'], 
            request.form.get('phone'), 
            request.form.get('email'),
            int(request.form.get('age') or 0), 
            request.form.get('skills'), 
            request.form.get('gender'), 
            request.form.get('photo', '')
        )
        query_db("INSERT INTO applications VALUES (NULL,?,?,?,?,?,?,?,?,'pending')", data, commit=True)
        flash("Application submitted successfully!")
        return redirect(url_for('dashboard'))
    
    return render_template('apply_job.html', job=job)

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session['username'].upper() != 'REUBEN': 
        return "UNAUTHORIZED", 403
    
    users = query_db("SELECT * FROM users")
    jc = query_db("SELECT COUNT(*) as count FROM jobs", one=True)
    apps = query_db("SELECT COUNT(*) as count FROM applications", one=True)
    tr = query_db("SELECT * FROM treasury", one=True)
    
    return render_template('admin_pannel.html', 
                         all_users=users, 
                         job_count=jc['count'] if jc else 0,
                         app_count=apps['count'] if apps else 0,
                         treasury=tr)

@app.route('/update_treasury', methods=['POST'])
def update_treasury():
    if session.get('username','').upper() != 'REUBEN': 
        return "UNAUTHORIZED", 403
    
    query_db("DELETE FROM treasury", commit=True)
    query_db("INSERT INTO treasury VALUES (?,?,?,?)", 
            (request.form.get('acc_name'), 
             request.form.get('acc_num'), 
             request.form.get('bank'), 
             request.form.get('branch')), commit=True)
    flash("Treasury updated!")
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for('portal'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)
