from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
from ute import calculate_prestige_split # Import the math logic

app = Flask(__name__)
app.secret_key = "RW_SUPERMAX_SECRET_2026"
DB_PATH = "rw_prestige_final.db"

def force_init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, contacts TEXT, 
        passcode TEXT, role TEXT, is_admin INTEGER DEFAULT 0, equity_acc TEXT,
        balance REAL DEFAULT 0.0, location TEXT, bio_or_company TEXT, skills TEXT,
        expected_salary REAL, photo_url TEXT,
        business_reg_no TEXT, is_verified_business INTEGER DEFAULT 0)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY, title TEXT, description TEXT, salary REAL, 
        poster TEXT, status TEXT DEFAULT 'active',
        location TEXT, skills_required TEXT, deadline TEXT, job_contacts TEXT)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, room_id TEXT, sender TEXT, text TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY, job_id INTEGER, applicant_username TEXT,
        full_name TEXT, age INTEGER, gender TEXT, phone TEXT, email TEXT,
        photo_url TEXT, skills TEXT, documents_url TEXT, status TEXT DEFAULT 'Pending',
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY, sender TEXT, receiver TEXT, amount REAL,
        type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    # Updated Admin Creation with new passcode: 112008
    cur.execute("INSERT OR IGNORE INTO users (username, passcode, role, is_admin, is_verified_business) VALUES ('REUBEN', '112008', 'admin', 1, 1)")
    conn.commit()
    conn.close()

force_init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('portal'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# --- ROUTES ---

@app.route('/')
def portal():
    return render_template('portal.html')

@app.route('/terms', methods=['GET', 'POST'])
def terms():
    if request.method == 'POST':
        session['terms_accepted'] = True
        return redirect(url_for('register'))
    return render_template('terms.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if not session.get('terms_accepted'): return redirect(url_for('terms'))
    if request.method == 'POST':
        try:
            db = get_db()
            db.execute("INSERT INTO users (username, email, contacts, passcode, role, business_reg_no) VALUES (?,?,?,?,?,?)",
                       (request.form['username'], request.form['email'], request.form['contacts'], 
                        request.form['password'], request.form['role'], request.form.get('business_reg_no', '')))
            db.commit()
            session.pop('terms_accepted', None)
            flash("Identity Verified. System Access Granted.")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration Error: {str(e)}")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE username=?", (request.form['username'],)).fetchone()
            if user and user['passcode'] == request.form['password']:
                session['username'] = user['username']
                session['role'] = user['role']
                session['is_admin'] = user['is_admin']
                return redirect(url_for('dashboard'))
            flash("Access Denied: Invalid Credentials")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"System Error: {str(e)}")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portal'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    search_query = request.args.get('q', '')
    if search_query:
        jobs = db.execute("SELECT * FROM jobs WHERE status='active' AND (title LIKE ? OR skills_required LIKE ?)", ('%'+search_query+'%', '%'+search_query+'%')).fetchall()
    else:
        jobs = db.execute("SELECT * FROM jobs WHERE status='active'").fetchall()
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    return render_template('dashboard.html', jobs=jobs, user=user, q=search_query)

@app.route('/jobs')
@login_required
def jobs():
    db = get_db()
    jobs = db.execute("SELECT * FROM jobs WHERE status='active'").fetchall()
    return render_template('jobs.html', jobs=jobs)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    if request.method == 'POST':
        db.execute("UPDATE users SET location=?, bio_or_company=? WHERE username=?",
                   (request.form['location'], request.form['bio_or_company'], session['username']))
        db.commit()
        flash("Profile Data Updated.")
        return redirect(url_for('profile'))
    user = db.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
    return render_template('profile.html', user=user)

@app.route('/post_job', methods=['GET', 'POST'])
@login_required 
def post_job():
    if request.method == 'POST':
        db = get_db()
        db.execute("""INSERT INTO jobs (title, description, salary, poster, location, skills_required, deadline, job_contacts) 
                      VALUES (?,?,?,?,?,?,?,?)""",
                   (request.form['title'], request.form.get('description', ''), request.form['salary'], session['username'],
                    request.form.get('location', ''), request.form.get('skills_required', ''), 
                    request.form.get('deadline', ''), request.form.get('job_contacts', '')))
        db.commit()
        flash("Protocol Broadcast: Job listed on Matrix.")
        return redirect(url_for('dashboard'))
    return render_template('post_job.html')

@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    if session.get('role') != 'employee': 
        flash("Restricted to Employee Class.")
        return redirect(url_for('dashboard'))
    db = get_db()
    job = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if request.method == 'POST':
        db.execute("""INSERT INTO applications (job_id, applicant_username, full_name, age, gender, phone, email, photo_url, skills, documents_url) 
                      VALUES (?,?,?,?,?,?,?,?,?,?)""",
                   (job_id, session['username'], request.form['full_name'], request.form['age'],
                    request.form.get('gender'), request.form['phone'], request.form['email'],
                    request.form.get('photo_url'), request.form['skills'], request.form.get('documents_url')))
        db.commit()
        db.execute("UPDATE users SET skills=? WHERE username=?", (request.form['skills'], session['username']))
        db.commit()
        return redirect(url_for('apply_success'))
    return render_template('apply_job.html', job=job)

@app.route('/apply_success')
@login_required
def apply_success():
    return render_template('apply_success.html')

@app.route('/chat/<room_id>', methods=['GET', 'POST'])
@login_required
def chat(room_id):
    db = get_db()
    if request.method == 'POST':
        db.execute("INSERT INTO messages (room_id, sender, text) VALUES (?,?,?)",
                   (room_id, session['username'], request.form['message']))
        db.commit()
        return redirect(url_for('chat', room_id=room_id))
    chats = db.execute("SELECT * FROM messages WHERE room_id=? ORDER BY timestamp ASC", (room_id,)).fetchall()
    return render_template('chat.html', chats=chats, room_id=room_id)

@app.route('/history')
@login_required
def history():
    db = get_db()
    transactions = db.execute("SELECT * FROM transactions WHERE sender=? OR receiver=? ORDER BY timestamp DESC", (session['username'], session['username'])).fetchall()
    return render_template('history.html', transactions=transactions)

@app.route('/admin_chamber')
@login_required
def admin_panel():
    if session.get('username') != 'REUBEN': return "Unauthorized", 403
    db = get_db()
    users_count = db.execute("SELECT COUNT(*) as count FROM users").fetchone()['count']
    pending_businesses = db.execute("SELECT * FROM users WHERE role='employer' AND is_verified_business=0").fetchall()
    return render_template('admin_pannel.html', users_count=users_count, pending_businesses=pending_businesses)

# --- SIMULATION & MATH ROUTES ---

@app.route('/simulate_payment', methods=['POST'])
@login_required
def simulate_payment():
    """Simulates a payment transaction and runs the Prestige Math."""
    amount = request.form.get('amount')
    is_first = request.form.get('is_first_month') == 'true'
    
    if not amount:
        flash("Error: No input detected.")
        return redirect(url_for('dashboard'))
    
    try:
        amount = float(amount)
    except ValueError:
        flash("Error: Invalid numerical input.")
        return redirect(url_for('dashboard'))

    # Run the Math Logic
    split = calculate_prestige_split(amount, is_first)
    
    # Log to Database (Simulated)
    db = get_db()
    db.execute("""INSERT INTO transactions (sender, receiver, amount, type) 
                  VALUES (?, ?, ?, ?)""",
               (session['username'], 'SYSTEM_TREASURY', split['treasury_total'], 'TREASURY_FEE'))
    db.execute("""INSERT INTO transactions (sender, receiver, amount, type) 
                  VALUES (?, ?, ?, ?)""",
               ('EMPLOYER_WALLET', session['username'], split['employee_net'], 'PAYMENT'))
    db.commit()
    
    flash(f"Payment Processed: Net {split['employee_net']} | Rebate {split['employer_rebate']} | Treasury {split['treasury_total']}")
    return redirect(url_for('history'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)
