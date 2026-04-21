import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'RW_ULTIMATE_GOD_KEY_2026'
DB = "rw_master_system_v18.db"

def query_db(query, args=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    # CORE INFRASTRUCTURE
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, passcode TEXT, email TEXT, phone TEXT, role TEXT, is_verified INTEGER DEFAULT 0, photo_url TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, location TEXT, salary REAL, posted_by TEXT, skills_required TEXT, description TEXT)")
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
    user = query_db("SELECT * FROM users WHERE username = ?", (session['username'],), one=True)
    jobs = query_db("SELECT * FROM jobs ORDER BY id DESC")
    all_users = query_db("SELECT * FROM users") if user['role'] == 'admin' else []
    my_jobs = query_db("SELECT * FROM jobs WHERE posted_by = ?", (session['username'],))
    
    # Get applications for Employer's jobs
    incoming_apps = []
    if user['role'] == 'employer' or user['role'] == 'admin':
        incoming_apps = query_db("SELECT a.*, j.title as job_title FROM applications a JOIN jobs j ON a.job_id = j.id WHERE j.posted_by = ?", (session['username'],))

    return render_template('dashboard.html', user=user, jobs=jobs, all_users=all_users, my_jobs=my_jobs, incoming_apps=incoming_apps)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p, e, ph, r = request.form.get('username'), request.form.get('passcode'), request.form.get('email'), request.form.get('phone'), request.form.get('role')
        # REUBEN PROTECTION
        role = 'admin' if u.upper() == 'REUBEN' else r
        user = query_db("SELECT * FROM users WHERE username = ?", (u,), one=True)
        if not user:
            query_db("INSERT INTO users (username, passcode, email, phone, role) VALUES (?, ?, ?, ?, ?)", (u, p, e, ph, role), commit=True)
        session['username'] = u
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/terminate_admin/<int:uid>')
def terminate_admin(uid):
    target = query_db("SELECT * FROM users WHERE id = ?", (uid,), one=True)
    if target and target['username'].upper() == 'REUBEN':
        return "ERROR: GOD CANNOT BE TERMINATED", 403
    query_db("DELETE FROM users WHERE id = ?", (uid,), commit=True)
    return redirect(url_for('index'))

@app.route('/post_job', methods=['POST'])
def post_job():
    data = (request.form.get('title'), request.form.get('location'), request.form.get('salary'), session['username'], request.form.get('skills'))
    query_db("INSERT INTO jobs (title, location, salary, posted_by, skills_required) VALUES (?, ?, ?, ?, ?)", data, commit=True)
    return redirect(url_for('index'))

@app.route('/submit_application', methods=['POST'])
def submit_application():
    data = (request.form.get('job_id'), session['username'], request.form.get('full_name'), request.form.get('id_number'), request.form.get('phone'), request.form.get('email'), request.form.get('gender'), request.form.get('age'), request.form.get('location'), request.form.get('skills'), request.form.get('photo_url'))
    query_db("INSERT INTO applications (job_id, applicant_username, full_name, id_number, phone, email, gender, age, location, skills, photo_url) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data, commit=True)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
