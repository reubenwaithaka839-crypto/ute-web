from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "RW_SUPERMAX_SECRET_2026"

DB_PATH = "rw_prestige_final.db"

# CRITICAL: Create database directly inside app.py to prevent Render path errors
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
        poster TEXT, status TEXT DEFAULT 'active')""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY, room_id TEXT, sender TEXT, text TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY, job_id INTEGER, applicant_username TEXT,
        full_name TEXT, age INTEGER, gender TEXT, phone TEXT, email TEXT,
        photo_url TEXT, skills TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY, sender TEXT, receiver TEXT, amount REAL,
        type TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")

    cur.execute("INSERT OR IGNORE INTO users (username, passcode, role, is_admin, is_verified_business) VALUES ('REUBEN', 'GOD_MODE_2026', 'admin', 1, 1)")
    conn.commit()
    conn.close()

# Run this immediately when Render starts
force_init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- PROTECTION DECORATORS ---
def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session: return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

def employer_verified_required(f):
    def wrap(*args, **kwargs):
        if session.get('role') != 'employer': return redirect(url_for('dashboard'))
        db = get_db()
        user = db.execute("SELECT is_verified_business FROM users WHERE username=?", (session['username'],)).fetchone()
        if not user or user['is_verified_business'] != 1:
            flash("Access Denied: Your business registration is pending admin verification.")
            return redirect(url_for('dashboard'))
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
    if not session.get('terms_accepted'):
        return redirect(url_for('terms'))
    
    if request.method == 'POST':
        db = get_db()
        reg_no = request.form.get('business_reg_no', '')
        
        try:
            db.execute("""INSERT INTO users (username, email, contacts, passcode, role, business_reg_no) 
                          VALUES (?,?,?,?,?,?)""",
                       (request.form['username'], request.form['email'], request.form['contacts'], 
                        request.form['password'], request.form['role'], reg_no))
            db.commit()
            session.pop('terms_accepted', None)
            flash("Identity registered. Awaiting login.")
            return redirect(url_for('login'))
        except Exception as e:
            flash("Error: Identity already exists or invalid data.")
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (request.form['username'],)).fetchone()
        if user and user['passcode'] == request.form['password']:
            session['username'] = user['username']
            session['role'] = user['role']
            session['is_admin'] = user['is_admin']
            return redirect(url_for('dashboard'))
        flash("Access Denied: Invalid
